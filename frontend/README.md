# frontend

Vue 3 前端工程目录，开发阶段按以下结构组织：

```
frontend/
├── src/
│   ├── api/                 # Axios 封装与接口定义
│   ├── assets/              # 静态资源
│   ├── components/          # 通用组件
│   ├── layouts/             # 布局（学生端 / 驿站工作台 / 管理端）
│   ├── router/              # 路由与权限守卫
│   ├── stores/              # Pinia 状态管理
│   ├── views/               # 页面
│   └── utils/               # 工具函数
├── public/
├── index.html
├── vite.config.js
├── package.json
└── Dockerfile
```

开发模式通过 Vite 代理将 `/api` 转发到 `http://localhost:8000`。
