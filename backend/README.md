# backend

FastAPI 后端服务目录，开发阶段按以下结构组织：

```
backend/
├── app/
│   ├── main.py              # 应用入口、路由注册、中间件
│   ├── core/                # 配置、安全、依赖注入、异常处理
│   ├── models/              # SQLAlchemy ORM 模型
│   ├── schemas/             # Pydantic 请求/响应模型
│   ├── api/v1/              # 按模块划分的路由
│   ├── services/            # 业务逻辑
│   └── utils/               # 工具函数
├── alembic/                 # 数据库迁移
├── tests/                   # 单元测试与接口测试
├── requirements.txt
└── Dockerfile
```

接口前缀统一为 `/api/v1`，自动生成的 OpenAPI 文档位于 `/docs`。
