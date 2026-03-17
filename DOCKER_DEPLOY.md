# Docker Compose 部署教程

本教程介绍如何使用 Docker Compose 部署小说生成器 Web 版。

## 前置要求

- Docker >= 20.10
- Docker Compose >= 2.0

## 部署步骤

### 1. 构建并启动容器

```bash
docker-compose up -d --build
```

### 2. 查看容器状态

```bash
docker-compose ps
```

### 3. 查看日志

```bash
docker-compose logs -f
```

### 4. 访问应用

容器启动后，在浏览器中打开：

```
http://localhost:7860/static/index.html
```

### 5. 停止服务

```bash
docker-compose down
```

## 使用说明

### 1. 配置 API

在网页中配置 LLM 和 Embedding：
- 选择接口类型（DeepSeek/OpenAI/Ollama 等）
- 输入 API Key、Base URL、模型名称
- 配置Embedding相关参数
- 点击"保存配置"

### 2. 创建小说

- 输入小说名称
- 点击"创建"按钮

### 3. 生成章节

- 选择章节编号和目标字数
- 点击"生成章节"

### 4. 编辑/定稿

- 切换到"编辑章节"标签
- 选择要编辑的章节
- 修改内容后点击"保存"
- 点击"定稿"完成章节

## 数据持久化

项目数据保存在 `data` 目录：
- `data/config.json` - API 配置
- `data/novels/` - 小说文件

## 常见问题

### 容器启动失败

```bash
docker-compose logs
```

查看错误日志。

### 内存不足

调整 docker-compose.yml 中的内存限制：

```yaml
deploy:
  resources:
    limits:
      memory: 16G
```
