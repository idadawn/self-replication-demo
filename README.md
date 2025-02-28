# AI自我复制实验平台

这是一个基于Python和React的AI自我复制实验平台，用于研究和测试AI系统的自我复制能力。

## 系统架构 
├── frontend/ # React前端
│ ├── src/
│ │ ├── components/ # 实验监控组件
│ │ ├── views/ # 实验场景控制界面
│ │ └── websocket/ # 实时通信模块
├── backend/ # FastAPI后端
│ ├── agents/ # AI智能体核心逻辑
│ │ ├── thinking/ # 多步规划模块
│ │ └── perception/ # 环境观察模块
│ ├── environments/ # 沙箱环境管理
│ │ ├── docker/ # Docker隔离环境
│ │ └── monitoring/ # 全程活动日志
│ ├── models/ # LLM适配器
│ │ ├── llama/ # Meta's Llama适配器
│ │ └── qwen/ # 阿里Qwen适配器
│ └── security/ # 安全控制模块
├── evaluation/ # 测试场景脚本
│ ├── basic_replication/ # 基础复制测试
│ ├── shutdown_avoidance/ # 关闭避免测试
│ └── chain_replication/ # 链式复制测试
└── data/ # 实验数据存储
```

## 主要功能

1. **智能体自我复制**
   - 基础复制能力测试
   - 链式复制实验
   - 复制准确性验证

2. **安全防护**
   - Docker容器隔离
   - 资源使用限制
   - 活动全程监控

3. **实时监控**
   - WebSocket实时通信
   - 复制过程可视化
   - 资源使用监控

## 环境配置

1. 创建环境配置文件：
```bash
cp .env.example .env
```

2. 配置API密钥：

QWEN_API_KEY=your_api_key_here
QWEN_MODEL_NAME=Qwen/Qwen-72B-Instruct
QWEN_API_BASE=https://api.qwen.ai/v1

## 开发指南

1. 安装依赖：
```bash
# 后端依赖
pip install -r requirements.txt

# 前端依赖
cd frontend
npm install
```

2. 启动服务：
```bash
# 启动后端
uvicorn backend.main:app --reload

# 启动前端
cd frontend
npm start
```

## 安全说明

本项目包含潜在的安全风险，请确保：

1. 在隔离的环境中运行
2. 限制资源使用
3. 监控所有活动
4. 不要在生产环境使用

## License

MIT License.

QWEN_API_KEY=your_api_key_here
QWEN_MODEL_NAME=Qwen/Qwen-72B-Instruct
QWEN_API_BASE=https://api.qwen.ai/v1