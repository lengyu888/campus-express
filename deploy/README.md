# deploy

Docker 编排与环境配置目录，规划文件：

| 文件 | 用途 |
| --- | --- |
| `docker-compose.yml` | 全栈一键启动：mysql、redis、backend、frontend |
| `docker-compose.infra.yml` | 仅启动 mysql 与 redis，供本地开发使用 |
| `.env.example` | 数据库口令、JWT 密钥、端口等环境变量样例 |
| `mysql/init/` | 首次启动执行的建库与初始化 SQL |

所有成员通过同一份镜像版本启动数据库，避免"我这里能跑"的环境差异。
