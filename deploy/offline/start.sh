#!/usr/bin/env bash
# 校园快递收发系统 · 离线一键启动（macOS / Linux / WSL）
set -e
cd "$(dirname "$0")"

echo "[1/3] 导入镜像（约 334 MB，首次需要 1-2 分钟）"
docker load -i images.tar.gz

echo "[2/3] 启动服务"
docker compose up -d

echo "[3/3] 等待后端健康检查（首次会建表并写入演示数据）"
for i in $(seq 1 40); do
  status=$(docker inspect -f '{{.State.Health.Status}}' campus-backend 2>/dev/null || echo starting)
  echo "  第 ${i} 次探测：${status}"
  [ "$status" = "healthy" ] && break
  sleep 3
done

echo
echo "启动完成"
echo "  系统首页：http://localhost"
echo "  接口文档：http://localhost:8000/docs"
echo "  演示账号：admin / Admin@123"
