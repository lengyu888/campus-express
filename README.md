# 校园快递收发系统（Campus Express）

[![CI](https://github.com/lengyu888/campus-express/actions/workflows/ci.yml/badge.svg)](https://github.com/lengyu888/campus-express/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> 软件工程课程设计 · 项目组  
> 技术栈：Vue 3 + FastAPI + MySQL 8.0（Docker）

## 1. 项目简介

面向高校校园场景的快递收发管理系统，覆盖快递到站入库、上架、取件码通知、核验出库、超期退回，以及学生寄件下单、驿站揽收的完整业务闭环。系统按"多驿站"模型设计，支持学生、驿站工作人员、系统管理员三类角色。

## 2. 技术选型

| 层次 | 技术 |
| --- | --- |
| 前端 | Vue 3 + Vite + Element Plus + Pinia + Vue Router + Axios |
| 后端 | Python 3.12 + FastAPI + SQLAlchemy 2.0 + Pydantic v2 + Alembic |
| 数据库 | MySQL 8.0（Docker 镜像） |
| 缓存 | Redis 7（Docker 镜像，用于取件码与登录态） |
| 鉴权 | JWT（Access Token + Refresh Token） |
| 部署 | Docker Compose（本地可前后端分离启动） |

## 3. 仓库结构

```
Campus_Express/
├── backend/                 # FastAPI 后端（app / alembic / seed）
├── frontend/                # Vue 3 前端（views / router / stores / api）
├── deploy/                  # Docker Compose 编排与 MySQL 初始化
├── docs/
│   ├── 系统设计文档.*        # 设计文档（md / docx / pdf）
│   ├── 交付物/              # 业务流程图、功能分析表、数据分析表、数据库表结构
│   ├── 阶段验收/            # 各阶段验收单
│   └── assets/              # 设计图源文件
├── scripts/                 # 绘图、文档生成、接口冒烟测试
├── .github/workflows/       # GitHub Actions 持续集成
├── LICENSE                  # MIT
└── README.md
```

> 课程提供的原始材料（`范例及模版/`、课程要求 PPT）仅在本地保留，已通过 `.gitignore` 排除，不入版本库。

## 4. 启动方式

系统规划两种启动方式，均使用 Docker 中的数据库镜像，保证组内成员环境一致：

### 4.1 本地开发模式

```bash
# 1) 只启动数据库与缓存
cp deploy/.env.example deploy/.env
docker compose -f deploy/docker-compose.infra.yml up -d

# 2) 后端
cd backend
python -m venv .venv && .venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload --port 8000

# 3) 前端
cd frontend && npm install && npm run dev
```

访问 `http://localhost:5173`。

### 4.2 Docker 一键启动

```bash
cp deploy/.env.example deploy/.env
docker compose -f deploy/docker-compose.yml up -d --build
```

访问 `http://localhost` 进入系统，`http://localhost:8000/docs` 查看接口文档。

> 两种方式共用 `deploy/` 下的数据卷，切换前先停止当前方式（`docker compose ... down`，不要加 `-v`）。
> 演示账号：`admin / Admin@123`、`staff01 / Staff@123`、`2023010101 / Student@123`。

## 5. 当前进度

- [x] 仓库初始化与目录规划
- [x] 系统设计文档（总体结构、数据库、接口、详细设计、部署设计）
- [x] 设计图：模块结构图、E-R 图、流程图、N-S 图、部署图、业务流程图（泳道图）
- [x] 需求分析交付物：业务流程图、功能分析表、数据分析表
- [x] 数据库表结构交付物（按课程模板）
- [x] 需求分析交付物（业务流程图、数据分析表、功能分析表）
- [x] **阶段一：基础设施 + 认证 + 用户管理（已验收、已提交）**
- [x] **阶段二：驿站与货架管理（已验收、已提交）**
- [x] **阶段三：快递入库与取件出库（已验收、已提交）**
- [x] **阶段四：寄件、通知与统计（已验收、已提交）**
- [x] **阶段五：异常、日志与测试验收（待验收）**
- [ ] 界面原型（每个功能项一张原型图）
- [x] 测试用例与 BUG 清单（56 条用例、12 个缺陷）
- [ ] 项目总结与答辩材料（答辩前准备）

## 6. 文档

- [系统设计文档（Markdown）](docs/系统设计文档.md)
- [系统设计文档（Word）](docs/系统设计文档.docx)
- [系统设计文档（PDF 预览）](docs/系统设计文档.pdf)
- [业务流程图（Word）](docs/交付物/业务流程图.docx)
- [功能分析表（Excel）](docs/交付物/功能分析表.xlsx)
- [数据分析表（Excel）](docs/交付物/数据分析表.xlsx)
- [数据库表结构（Excel）](docs/交付物/数据库表结构.xlsx)
- [测试用例与 BUG 清单（Excel）](docs/交付物/测试用例与BUG清单.xlsx)
- [部署说明](docs/部署说明.md)
- [阶段一验收单](docs/阶段验收/阶段一-认证与用户.md)
- [阶段二验收单](docs/阶段验收/阶段二-驿站与货架.md)
- [阶段三验收单](docs/阶段验收/阶段三-快递入库与取件.md)
- [阶段四验收单](docs/阶段验收/阶段四-寄件通知与统计.md)
- [阶段五验收单](docs/阶段验收/阶段五-异常日志与测试验收.md)
- [设计图源文件](docs/assets)

设计阶段已确认的关键决策：

| 决策项 | 结论 |
| --- | --- |
| 业务范围 | 收件闭环 + 基础寄件 |
| 取件核验 | 取件码 + 手机号后四位 |
| 驿站模型 | 多驿站、多货架 |
| 数据库 | MySQL 8.0（Docker 镜像） |
| 文档形态 | Word 提交版 + Markdown 源文件 |

## 7. 性能与运维

- 统计接口合并为聚合查询：总览 4 条 SQL（原 13 条）、驿站工作量 1 条（原 4N 条）
- 组合索引：`packages(status, stored_at)`、`operation_logs(created_at)`、`exception_records(status, created_at)`
- 连接池：`pool_size=10`、`max_overflow=20`、`pool_pre_ping`、`pool_recycle=1800`
- 前端按依赖分包（vue / element-plus / axios / vendor），首屏入口从 1.14 MB 降到 11 KB，静态资源长缓存
- 容器：后端以非 root（uid 1001）运行，后端健康检查通过后前端才启动
- 运维脚本：
  - `python -m app.tasks.overdue_scan --dry-run`：扫描超期包裹并推送提醒（建议每日定时执行）
  - `python scripts/cleanup_logs.py --days 90 --dry-run`：清理历史日志与已读通知

## 8. 持续集成

`.github/workflows/ci.yml` 在推送到 `main` 与提交 Pull Request 时自动执行：

| 任务 | 内容 |
| --- | --- |
| 后端冒烟（阶段 1–5 并行） | 每个阶段独立启动 MySQL 8.0 + Redis 7 服务容器 → Alembic 迁移 → 灌入演示数据 → 启动服务 → 执行该阶段接口测试 |
| 前端构建 | `npm ci` + `npm run build`，产物作为 Artifact 保留 3 天 |
| 编排校验 | `docker compose config` 校验两份 Compose 文件的语法与环境变量 |

本地等价命令：`python scripts/smoke_stage{1..5}.py`（需后端已启动在 8000 端口）。

## 9. 许可证

本项目采用 [MIT License](LICENSE)，可自由用于学习与二次开发，请保留版权声明。

## 10. 协作约定

- 分支模型：`main` 为稳定分支，功能开发走 `feature/<模块名>`，合并前提交 Pull Request。
- 提交信息：`feat:` / `fix:` / `docs:` / `refactor:` / `test:` / `chore:` 前缀。
- 数据库变更一律通过 Alembic 迁移脚本，禁止手工改表后不入库。
- 环境变量统一从 `.env` 读取，仓库只提交 `.env.example`。
