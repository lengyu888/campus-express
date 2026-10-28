#!/bin/sh
set -e

echo "[entrypoint] 执行数据库迁移..."
alembic upgrade head

echo "[entrypoint] 初始化演示账号..."
python -m app.seed

echo "[entrypoint] 启动后端服务..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
