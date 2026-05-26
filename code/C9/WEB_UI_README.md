# C9 Graph RAG 可视化控制台启动与使用说明

本文档说明如何启动 Chapter 9 的 Graph RAG 烹饪助手可视化页面。后端使用 Flask，前端使用 Vue3，核心问答能力复用原控制台程序 `main.py` 中的 `AdvancedGraphRAGSystem`。

## 目录结构

```text
code/C9/
├── api_server.py              # Flask 后端入口，托管 API 和前端 dist
├── main.py                    # 原 Python 控制台程序
├── requirements.txt           # Python 依赖
├── conda环境                  # 当前项目环境说明：conda activate graph-rag
├── frontend/                  # Vue3 前端项目
│   ├── src/
│   ├── package.json
│   └── dist/                  # npm run build 后生成，Flask 会托管这里
└── rag_modules/               # Graph RAG 核心模块
```

## 1. 启动基础服务

C9 依赖 Neo4j 图数据库。先在项目根目录启动 Docker 服务：

```powershell
cd D:\project\LearnAgent\all-in-rag\data\C9
docker compose up -d
```

确认 Neo4j 容器正常：

```powershell
docker ps
```

Neo4j Web UI：

```text
http://127.0.0.1:7474
```

默认账号密码：

```text
用户名：neo4j
密码：all-in-rag
```

Bolt 地址：

```text
bolt://localhost:7687
```

如果你还使用 Milvus，请确保 Milvus 服务也已启动，并且端口与 `config.py` 中一致：

```text
localhost:19530
```

## 2. 激活 Python 环境

本项目使用的 conda 环境是：

```powershell
conda activate graph-rag
```

确认当前 Python 来自 `graph-rag` 环境：

```powershell
python -c "import sys; print(sys.executable)"
```

安装或补齐依赖：

```powershell
cd D:\project\LearnAgent\all-in-rag\code\C9
python -m pip install -r requirements.txt
```

如果只缺某个包，也可以单独安装，例如：

```powershell
python -m pip install neo4j Flask
```

注意：报错 `No module named 'neo4j'` 指的是 Python 客户端包没有安装到当前 Python 环境，不是 Neo4j 数据库服务没安装。

## 3. 构建前端页面

第一次运行或修改前端代码后，需要构建 Vue3 页面：

```powershell
cd D:\project\LearnAgent\all-in-rag\code\C9\frontend
npm install
npm run build
```

构建成功后会生成：

```text
code/C9/frontend/dist/
```

Flask 会自动托管这个目录。

## 4. 启动 Flask 后端和页面

进入 C9 目录：

```powershell
cd D:\project\LearnAgent\all-in-rag\code\C9
conda activate graph-rag
python api_server.py
```

看到以下输出说明服务已启动：

```text
 * Running on http://127.0.0.1:5000
```

浏览器打开：

```text
http://127.0.0.1:5000
```

同一个地址既提供前端页面，也提供后端 API：

```text
前端页面：http://127.0.0.1:5000
健康检查：http://127.0.0.1:5000/api/health
统计接口：http://127.0.0.1:5000/api/stats
配置接口：http://127.0.0.1:5000/api/config
```

`/api/health` 会返回当前后端实际使用的 Python 路径：

```json
{
  "runtime": {
    "python_executable": "E:\\anaconda3\\envs\\graph-rag\\python.exe"
  }
}
```

如果这里不是 `graph-rag` 环境，说明 5000 端口上跑的是旧进程或错误环境。

## 5. 页面使用流程

推荐按这个顺序操作：

1. 打开 `http://127.0.0.1:5000`
2. 点击右上角「初始化」
3. 等待状态显示初始化结果
4. 点击「构建」
5. 等待知识库加载或构建完成
6. 在「问答」页面输入问题并发送

页面主要功能：

- 「问答」：提交烹饪问题，查看 RAG 回答和路由分析摘要
- 「统计」：查看菜谱、食材、步骤、文本块、路由次数等统计
- 「路由」：单独分析一个问题会走传统混合检索、Graph RAG，还是组合策略
- 「配置」：在系统初始化前调整 Neo4j、Milvus、模型、chunk、top_k 等参数
- 「重建知识库」：删除当前 Milvus 集合并重新从 Neo4j 加载、分块、建索引

## 6. 开发模式

如果你要开发前端，可以单独启动 Vite：

```powershell
cd D:\project\LearnAgent\all-in-rag\code\C9\frontend
npm run dev
```

前端开发地址：

```text
http://127.0.0.1:5173
```

此时 API 会通过 `vite.config.js` 代理到 Flask：

```text
http://127.0.0.1:5000
```

所以开发模式需要同时启动两个服务：

```powershell
# 终端 1：后端
cd D:\project\LearnAgent\all-in-rag\code\C9
conda activate graph-rag
python api_server.py

# 终端 2：前端
cd D:\project\LearnAgent\all-in-rag\code\C9\frontend
npm run dev
```

## 7. 关闭服务

在运行 Flask 的终端按：

```text
Ctrl + C
```

如果找不到终端，可以按端口查进程：

```powershell
netstat -ano | findstr :5000
```

最后一列是 PID，然后关闭：

```powershell
Stop-Process -Id PID
```

关闭 Docker 服务：

```powershell
cd D:\project\LearnAgent\all-in-rag\data\C9
docker compose down
```

## 8. 常见问题

### 页面只有背景色，没有任何元素

先强制刷新：

```text
Ctrl + F5
```

如果仍然空白，打开浏览器开发者工具 `F12`，查看 Console 的第一条红色错误。

常见原因：

- 前端没有重新构建：执行 `npm run build`
- Flask 还在托管旧的 `dist`：重启 `python api_server.py`
- JS MIME 类型错误：当前 `api_server.py` 已显式注册 `.js` 为 `application/javascript`

### `GET /favicon.ico 404`

这个不是功能错误，只是浏览器请求网站图标。当前前端已用空 favicon 避免该日志。

### 初始化失败：`No module named 'neo4j'`

说明当前运行 Flask 的 Python 环境没有安装 `neo4j` Python 包。

先确认环境：

```powershell
conda activate graph-rag
python -c "import sys; print(sys.executable)"
```

再安装：

```powershell
python -m pip install neo4j
```

### 控制台程序能跑，但 Web 页面初始化缺包

这通常是两个入口使用了不同 Python 环境。

请确保启动 Flask 前先执行：

```powershell
conda activate graph-rag
python api_server.py
```

不要用其他环境的绝对路径启动 `api_server.py`。

可以用下面命令确认 5000 端口当前进程：

```powershell
netstat -ano | findstr :5000
Get-Process -Id PID | Select-Object Id,ProcessName,Path
```

如果显示的是其他环境，例如 `all-in-rag`，先关闭旧进程：

```powershell
Stop-Process -Id PID
```

再用 `graph-rag` 重启。

### 修改配置后没有生效

页面上的配置只允许在系统初始化前修改。系统已经初始化后，需要：

1. 关闭 Flask
2. 重新启动 `python api_server.py`
3. 在页面「配置」中修改
4. 再点击「初始化」

### 端口 5000 被占用

可以换端口启动：

```powershell
$env:C9_WEB_PORT=5050
python api_server.py
```

然后打开：

```text
http://127.0.0.1:5050
```

## 9. 推荐的一键启动顺序

```powershell
# 1. 启动 Neo4j
cd D:\project\LearnAgent\all-in-rag\data\C9
docker compose up -d

# 2. 激活 Python 环境
cd D:\project\LearnAgent\all-in-rag\code\C9
conda activate graph-rag

# 3. 构建前端，如果 dist 已经是最新可跳过
cd frontend
npm install
npm run build

# 4. 启动 Web 控制台
cd ..
python api_server.py
```

打开：

```text
http://127.0.0.1:5000
```
