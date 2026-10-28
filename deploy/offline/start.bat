@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo [1/3] 导入镜像（约 334 MB，首次需要 1-2 分钟）
docker load -i images.tar.gz
if errorlevel 1 goto fail

echo [2/3] 启动服务
docker compose up -d
if errorlevel 1 goto fail

echo [3/3] 等待后端健康检查（首次会建表并写入演示数据）
timeout /t 45 /nobreak >nul

echo.
echo 启动完成
echo   系统首页：http://localhost
echo   接口文档：http://localhost:8000/docs
echo   演示账号：admin / Admin@123
echo.
docker compose ps
pause
exit /b 0

:fail
echo.
echo 启动失败：请确认 Docker Desktop 已启动并处于运行状态
pause
exit /b 1
