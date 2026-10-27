# backend

FastAPI 后端，阶段一已实现认证与用户管理。

```
backend/
├── app/
│   ├── main.py              # 应用入口、中间件、异常处理、健康检查
│   ├── core/                # 配置、安全、依赖、Redis、统一响应
│   ├── db/                  # 引擎与会话
│   ├── models/              # SQLAlchemy 模型
│   ├── schemas/             # Pydantic 模型
│   ├── api/v1/              # 路由（auth、users）
│   └── seed.py              # 演示账号初始化
├── alembic/                 # 数据库迁移
├── requirements.txt
└── Dockerfile
```

本地启动：

```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload --port 8000
```

接口文档：http://localhost:8000/docs
