# -*- coding: utf-8 -*-
"""构建离线部署包（镜像 + 编排 + 启动脚本 + 说明）。

用法：
    python scripts/build_offline_package.py
    python scripts/build_offline_package.py --version 1.0.1

产物：dist-offline/campus-express-offline-<version>.zip

前置：本地已通过 docker compose 构建过后端与前端镜像（deploy-backend / deploy-frontend）。
"""
import argparse
import gzip
import secrets
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "deploy" / "offline"
STAGING = ROOT / "dist-offline" / "campus-express-offline"
OUTPUT_DIR = ROOT / "dist-offline"

# 应用镜像由 compose 构建，导出前统一打上版本标签
APP_IMAGES = {
    "deploy-backend:latest": "campus-express/backend",
    "deploy-frontend:latest": "campus-express/frontend",
}
THIRD_PARTY_IMAGES = ["mysql:8.0", "redis:7-alpine"]

TEMPLATE_FILES = ["docker-compose.yml", "start.sh", "start.bat", "启动说明.md"]


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    print("  $", " ".join(cmd))
    return subprocess.run(cmd, check=True, **kwargs)


def docker_ok() -> bool:
    try:
        subprocess.run(["docker", "info"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def tag_images(version: str) -> list[str]:
    tagged = []
    for source, target in APP_IMAGES.items():
        full = f"{target}:{version}"
        try:
            run(["docker", "tag", source, full], capture_output=True)
            tagged.append(full)
        except subprocess.CalledProcessError:
            print(f"  ! 缺少镜像 {source}，请先执行：")
            print("    docker compose -f deploy/docker-compose.yml --env-file deploy/.env build")
            raise SystemExit(1)
    return tagged + THIRD_PARTY_IMAGES


def save_images(images: list[str], target: Path) -> None:
    """docker save 四个镜像并 gzip 压缩，避免在内存里拼装。"""
    print(f"[1/4] 导出镜像 → {target.name}")
    with target.open("wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", compresslevel=6) as gz:
        proc = subprocess.Popen(["docker", "save", *images], stdout=subprocess.PIPE)
        assert proc.stdout is not None
        shutil.copyfileobj(proc.stdout, gz, length=1024 * 1024)
        code = proc.wait()
    if code != 0:
        raise SystemExit("docker save 失败")


def write_env(target: Path) -> None:
    # 密码只用字母数字：@ : / # ? 等字符会让 DATABASE_URL 解析错位
    target.write_text(
        "# ===== 校园快递收发系统 · 离线部署环境变量 =====\n"
        "# 端口被占用时改这两项，例如 BACKEND_PORT=18000、FRONTEND_PORT=8080\n"
        "FRONTEND_PORT=80\n"
        "BACKEND_PORT=8000\n"
        "\n"
        "# ===== MySQL =====\n"
        "# 注意：密码请只用字母数字，含 @ : / # ? 会破坏 DATABASE_URL 解析\n"
        f"MYSQL_ROOT_PASSWORD=Root{secrets.token_hex(6)}\n"
        "MYSQL_DATABASE=campus_express\n"
        "MYSQL_USER=campus\n"
        f"MYSQL_PASSWORD=Campus{secrets.token_hex(6)}\n"
        "\n"
        "# ===== 鉴权 =====\n"
        f"JWT_SECRET={secrets.token_urlsafe(36)}\n"
        "ACCESS_TOKEN_EXPIRE_MINUTES=120\n"
        "REFRESH_TOKEN_EXPIRE_DAYS=7\n"
        "\n"
        "# ===== 其他 =====\n"
        "TZ=Asia/Shanghai\n",
        encoding="utf-8",
    )


def make_zip(source: Path, target: Path, prefix: str) -> None:
    print(f"[4/4] 打包 → {target.name}")
    with zipfile.ZipFile(target, "w") as zf:
        for path in sorted(source.rglob("*")):
            if path.is_dir():
                continue
            arcname = Path(prefix) / path.relative_to(source)
            # 已压缩的镜像包不再重复压缩，其余文本文件压缩
            method = zipfile.ZIP_STORED if path.suffix == ".gz" else zipfile.ZIP_DEFLATED
            zf.write(path, arcname, compress_type=method)


def main() -> None:
    parser = argparse.ArgumentParser(description="构建离线部署包")
    parser.add_argument("--version", default="1.0.0", help="应用镜像版本标签，默认 1.0.0")
    parser.add_argument("--keep-staging", action="store_true", help="保留解包前的中间目录")
    args = parser.parse_args()

    if not docker_ok():
        raise SystemExit("Docker 不可用，请先启动 Docker Desktop / dockerd")

    print(f"准备离线包 v{args.version}")
    images = tag_images(args.version)

    if STAGING.exists():
        shutil.rmtree(STAGING)
    (STAGING / "mysql-init").mkdir(parents=True)

    save_images(images, STAGING / "images.tar.gz")

    print("[2/4] 复制编排与启动脚本")
    for name in TEMPLATE_FILES:
        shutil.copy2(TEMPLATE / name, STAGING / name)
    (STAGING / "start.sh").chmod(0o755)
    # 批处理统一为 CRLF，避免 cmd 解析异常
    bat = STAGING / "start.bat"
    bat.write_bytes(bat.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))

    print("[3/4] 生成 .env 与 MySQL 初始化脚本")
    write_env(STAGING / ".env")
    shutil.copy2(ROOT / "deploy" / "mysql" / "init" / "01-init.sql", STAGING / "mysql-init")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = OUTPUT_DIR / f"campus-express-offline-v{args.version}.zip"
    if zip_path.exists():
        zip_path.unlink()
    make_zip(STAGING, zip_path, f"campus-express-offline-v{args.version}")

    if not args.keep_staging:
        shutil.rmtree(STAGING, ignore_errors=True)

    size_mb = zip_path.stat().st_size / 1024 / 1024
    print()
    print(f"完成：{zip_path}（{size_mb:.0f} MB）")
    print("使用者执行：解压 → docker load -i images.tar.gz → docker compose up -d")


if __name__ == "__main__":
    sys.exit(main())
