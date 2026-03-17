# web/main.py
# -*- coding: utf-8 -*-
import os
import json
import uuid
import logging
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from datetime import datetime
import asyncio

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="小说生成器API")

BASE_DIR = Path("/app/data")
NOVELS_DIR = BASE_DIR / "novels"
NOVELS_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory="templates"), name="static")
templates = Jinja2Templates(directory="templates")

tasks = {}

class GenerateRequest(BaseModel):
    novel_name: str
    word_number: int = 3000
    chapter_num: int = 1
    llm_config: dict
    embedding_config: dict

class FinalizeRequest(BaseModel):
    novel_name: str
    chapter_num: int
    chapter_content: str
    llm_config: dict
    embedding_config: dict

class ConfigRequest(BaseModel):
    llm_configs: dict
    embedding_config: dict

@app.get("/")
async def home():
    return {"message": "小说生成器API", "version": "1.0"}

@app.get("/ui")
async def ui():
    return {"message": "请访问 /static/index.html"}

@app.post("/api/config/save")
async def save_config(config: ConfigRequest):
    config_path = BASE_DIR / "config.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config.dict(), f, ensure_ascii=False, indent=2)
    return {"status": "success", "message": "配置已保存"}

@app.post("/api/novels")
async def create_novel(novel_name: str):
    novel_dir = NOVELS_DIR / novel_name
    if novel_dir.exists():
        return {"status": "error", "message": "小说已存在"}
    
    novel_dir.mkdir(parents=True)
    (novel_dir / "chapters").mkdir()
    
    return {"status": "success", "novel_dir": str(novel_dir)}

@app.get("/api/novels")
async def list_novels():
    if not NOVELS_DIR.exists():
        return {"novels": []}
    
    novels = []
    for d in NOVELS_DIR.iterdir():
        if d.is_dir():
            chapters_dir = d / "chapters"
            chapter_count = len(list(chapters_dir.glob("chapter_*.txt"))) if chapters_dir.exists() else 0
            novels.append({
                "name": d.name,
                "path": str(d),
                "chapter_count": chapter_count
            })
    return {"novels": novels}

@app.get("/api/novels/{novel_name}/chapters")
async def list_chapters(novel_name: str):
    novel_dir = NOVELS_DIR / novel_name
    if not novel_dir.exists():
        raise HTTPException(status_code=404, detail="小说不存在")
    
    chapters_dir = novel_dir / "chapters"
    chapters = []
    for f in sorted(chapters_dir.glob("chapter_*.txt")):
        chapter_num = f.stem.replace("chapter_", "")
        with open(f, "r", encoding="utf-8") as fp:
            content = fp.read()
        chapters.append({
            "number": chapter_num,
            "word_count": len(content),
            "preview": content[:200] if content else ""
        })
    
    return {"chapters": chapters}

@app.get("/api/novels/{novel_name}/chapters/{chapter_num}")
async def get_chapter(novel_name: str, chapter_num: int):
    chapter_file = NOVELS_DIR / novel_name / "chapters" / f"chapter_{chapter_num}.txt"
    if not chapter_file.exists():
        raise HTTPException(status_code=404, detail="章节不存在")
    
    with open(chapter_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    return {"content": content, "word_count": len(content)}

@app.put("/api/novels/{novel_name}/chapters/{chapter_num}")
async def update_chapter(novel_name: str, chapter_num: int, request: dict):
    novel_dir = NOVELS_DIR / novel_name
    if not novel_dir.exists():
        raise HTTPException(status_code=404, detail="小说不存在")
    
    chapter_file = novel_dir / "chapters" / f"chapter_{chapter_num}.txt"
    with open(chapter_file, "w", encoding="utf-8") as f:
        f.write(request.get("content", ""))
    
    return {"status": "success", "message": "章节已保存"}

@app.get("/api/config")
async def get_config():
    config_path = BASE_DIR / "config.json"
    if not config_path.exists():
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

@app.post("/api/generate/chapter")
async def generate_chapter(request: GenerateRequest, background_tasks: BackgroundTasks):
    from novel_generator.chapter import generate_chapter_text
    
    novel_dir = NOVELS_DIR / request.novel_name
    novel_dir.mkdir(parents=True, exist_ok=True)
    (novel_dir / "chapters").mkdir(exist_ok=True)
    
    task_id = str(uuid.uuid4())
    tasks[task_id] = {"status": "pending", "message": ""}
    
    async def run_generation():
        try:
            tasks[task_id]["status"] = "running"
            result = generate_chapter_text(
                novel_number=request.chapter_num,
                word_number=request.word_number,
                novel_name=request.novel_name,
                api_key=request.llm_config.get("api_key"),
                base_url=request.llm_config.get("base_url"),
                model_name=request.llm_config.get("model_name"),
                temperature=request.llm_config.get("temperature", 0.7),
                interface_format=request.llm_config.get("interface_format"),
                max_tokens=request.llm_config.get("max_tokens", 4096),
                timeout=request.llm_config.get("timeout", 600),
                filepath=str(novel_dir),
                embedding_api_key=request.embedding_config.get("api_key"),
                embedding_url=request.embedding_config.get("url"),
                embedding_interface_format=request.embedding_config.get("interface_format"),
                embedding_model_name=request.embedding_config.get("model_name")
            )
            
            chapter_file = novel_dir / "chapters" / f"chapter_{request.chapter_num}.txt"
            with open(chapter_file, "w", encoding="utf-8") as f:
                f.write(result)
            
            tasks[task_id]["status"] = "completed"
            tasks[task_id]["result"] = result
        except Exception as e:
            tasks[task_id]["status"] = "error"
            tasks[task_id]["message"] = str(e)
            logger.error(f"生成章节失败: {e}")
    
    background_tasks.add_task(run_generation)
    
    return {"task_id": task_id, "status": "started"}

@app.get("/api/tasks/{task_id}")
async def get_task_status(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    return tasks[task_id]

@app.post("/api/finalize/chapter")
async def finalize_chapter(request: FinalizeRequest, background_tasks: BackgroundTasks):
    from novel_generator.finalization import finalize_chapter as do_finalize
    
    novel_dir = NOVELS_DIR / request.novel_name
    
    chapter_file = novel_dir / "chapters" / f"chapter_{request.chapter_num}.txt"
    with open(chapter_file, "w", encoding="utf-8") as f:
        f.write(request.chapter_content)
    
    task_id = str(uuid.uuid4())
    tasks[task_id] = {"status": "pending", "message": ""}
    
    async def run_finalization():
        try:
            tasks[task_id]["status"] = "running"
            do_finalize(
                novel_number=request.chapter_num,
                word_number=len(request.chapter_content),
                api_key=request.llm_config.get("api_key"),
                base_url=request.llm_config.get("base_url"),
                model_name=request.llm_config.get("model_name"),
                temperature=request.llm_config.get("temperature", 0.7),
                filepath=str(novel_dir),
                embedding_api_key=request.embedding_config.get("api_key"),
                embedding_url=request.embedding_config.get("url"),
                embedding_interface_format=request.embedding_config.get("interface_format"),
                embedding_model_name=request.embedding_config.get("model_name"),
                interface_format=request.llm_config.get("interface_format"),
                max_tokens=request.llm_config.get("max_tokens", 4096),
                timeout=request.llm_config.get("timeout", 600)
            )
            tasks[task_id]["status"] = "completed"
        except Exception as e:
            tasks[task_id]["status"] = "error"
            tasks[task_id]["message"] = str(e)
            logger.error(f"定稿失败: {e}")
    
    background_tasks.add_task(run_finalization)
    
    return {"task_id": task_id, "status": "started"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
