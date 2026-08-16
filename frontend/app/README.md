# 前端应用（Vue 3 + Vite + TypeScript）

默认 Vue 界面。`frontend/src/` 下的旧版 Jinja 界面在 P15 后作为显式回滚入口保留。

```
/              本应用
/legacy[/]     旧版 Jinja fallback
/app/*         到对应 root 路径的临时兼容重定向
/api/*         两者共用的 JSON 接口
/assets/*      Vue 构建产物
/static/*      旧版静态资源
```

侧边栏底部的「旧版界面」使用普通链接进入 `/legacy/`，不属于 Vue Router。

## 环境要求

Node **24**（与 `package.json` 的 `engines`、`Dockerfile` 的 builder 阶段、CI
保持同一个大版本）。

## 常用命令

```bash
cd frontend/app

npm ci             # 按 package-lock.json 严格安装，不解析新版本
npm run dev        # 开发服务器，默认 http://localhost:5173/
npm run typecheck  # vue-tsc，strict 模式
npm run test:run   # Vitest 单次运行
npm run test       # Vitest watch 模式
npm run build      # 产物输出到 frontend/app/dist
```

## 开发时的后端

`npm run dev` 会把 `/api` 代理到后端，默认 `http://127.0.0.1:5001`（与
`config/config.yml` 的 `server.port` 一致）。需要指向别处时：

```bash
VITE_DEV_API_TARGET=http://127.0.0.1:5000 npm run dev
```

生产构建**不会**带入任何后端主机名：应用由回答 `/api` 的同一个 Flask 进程提供，
所以接口地址是同源相对路径 `/api`。

> `VITE_*` 变量会被编译进浏览器产物。只放 API 地址这类公开信息，绝不要放
> cookie、数据库口令或任何凭证。

## 生产

```bash
npm run build          # 生成 frontend/app/dist
python ./server.py     # Flask 从 dist 提供 root Vue 页面
```

未执行过 `npm run build` 时，`/` 和 Vue deep link 会明确返回 503；不会自动回退
旧界面。`/legacy/` 与 `/api/*` 仍可独立访问，因此坏镜像保持可见且人工 fallback
仍然存在。

## 目录

```
src/
├── api/          typed 后端客户端（client / resolve / tasks）
├── components/   布局组件
├── router/       路由表，base 取自 import.meta.env.BASE_URL
├── stores/       Pinia，目前只有 shell 状态
├── styles/       CSS 变量与全局样式
├── types/        与后端 wire contract 对齐的类型
└── views/        六个页面
tests/            Vitest，全部使用 mock fetch，不触网
```
