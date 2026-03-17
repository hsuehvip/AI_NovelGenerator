# Windows EXE 打包指南

本文档介绍如何将小说生成器打包成 Windows 可执行文件(EXE)。

## 环境要求

- Windows 10/11 系统
- Python 3.11
- 足够的磁盘空间（约3-5GB）

## 打包步骤

### 1. 安装依赖

```bash
pip install pyinstaller
pip install -r requirements.txt
```

### 2. 打包命令

```bash
pyinstaller main_gui.spec
```

### 3. 打包输出

打包完成后，EXE 文件位于：
```
dist/AI_NovelGenerator/AI_NovelGenerator.exe
```

## 注意事项

1. **customtkinter 路径**：如果打包失败，需要修改 `main_gui.spec` 中的 customtkinter 路径为你的实际安装路径

2. **图标文件**：确保 `icon.ico` 存在，否则去掉 icon 参数

3. **首次运行**：打包后的 EXE 首次运行可能较慢（需要解压）

## 常见问题

### 问题1：打包后运行报错缺少模块

解决：在 spec 文件的 hiddenimports 中添加缺失的模块

### 问题2：打包后界面显示异常

解决：确保 customtkinter 资源正确包含

### 问题3：打包后缺少依赖

解决：运行 `pyinstaller --onefile main.py --hidden-import=模块名`

## 简化打包（推荐）

如果上述 spec 文件打包失败，可以尝试简化方式：

```bash
pip install pyinstaller

pyinstaller --onefile ^
    --name AI_NovelGenerator ^
    --add-data "icon.ico;." ^
    --hidden-import=customtkinter ^
    --hidden-import=nltk ^
    --hidden-import=langchain ^
    --hidden-import=chromadb ^
    --collect-all=chromadb ^
    --collect-all=langchain ^
    --collect-all=langchain_chroma ^
    --console=False ^
    main.py
```

## Web 版本

如果需要 Web 版，请使用 Docker 部署：

```bash
docker-compose up -d --build
```

然后访问：`http://localhost:7860/static/index.html`
