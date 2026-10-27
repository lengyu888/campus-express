# 校园快递收发系统（Campus Express）

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
├── 软件工程课程设计PPT.pdf   # 课程要求原始材料
└── README.md
```

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
- [x] **阶段三：快递入库与取件出库（待验收）**
- [ ] 阶段四：寄件、通知与统计
- [ ] 阶段五：测试、部署与验收
- [ ] 界面原型（每个功能项一张原型图）
- [ ] 测试用例与 BUG 清单
- [ ] 项目总结与答辩材料

## 6. 文档

- [系统设计文档（Markdown）](docs/系统设计文档.md)
- [系统设计文档（Word）](docs/系统设计文档.docx)
- [系统设计文档（PDF 预览）](docs/系统设计文档.pdf)
- [业务流程图（Word）](docs/交付物/业务流程图.docx)
- [功能分析表（Excel）](docs/交付物/功能分析表.xlsx)
- [数据分析表（Excel）](docs/交付物/数据分析表.xlsx)
- [数据库表结构（Excel）](docs/交付物/数据库表结构.xlsx)
- [阶段一验收单](docs/阶段验收/阶段一-认证与用户.md)
- [阶段二验收单](docs/阶段验收/阶段二-驿站与货架.md)
- [阶段三验收单](docs/阶段验收/阶段三-快递入库与取件.md)
- [设计图源文件](docs/assets)

设计阶段已确认的关键决策：

| 决策项 | 结论 |
| --- | --- |
| 业务范围 | 收件闭环 + 基础寄件 |
| 取件核验 | 取件码 + 手机号后四位 |
| 驿站模型 | 多驿站、多货架 |
| 数据库 | MySQL 8.0（Docker 镜像） |
| 文档形态 | Word 提交版 + Markdown 源文件 |

## 7. 协作约定

- 分支模型：`main` 为稳定分支，功能开发走 `feature/<模块名>`，合并前提交 Pull Request。
- 提交信息：`feat:` / `fix:` / `docs:` / `refactor:` / `test:` / `chore:` 前缀。
- 数据库变更一律通过 Alembic 迁移脚本，禁止手工改表后不入库。
- 环境变量统一从 `.env` 读取，仓库只提交 `.env.example`。
