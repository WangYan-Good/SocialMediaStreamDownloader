# 前端应用（Vue 3 + Vite + TypeScript）

新界面。与 `frontend/src/` 下的旧版 Jinja 界面**并行存在**，不是替换关系。

```
/          旧版 Jinja 界面（目前仍是完整可用的产品）
/app/      本应用
/api/*     两者共用的 JSON 接口
```

新界面按阶段逐屏接入，在达到功能对等之前，旧版界面保持为正式入口。侧边栏底部
的「旧版界面」链接就是为此存在的。

## 环境要求

Node **24**（与 `package.json` 的 `engines`、`Dockerfile` 的 builder 阶段、CI
保持同一个大版本）。

## 常用命令

```bash
cd frontend/app

npm ci             # 按 package-lock.json 严格安装，不解析新版本
npm run dev        # 开发服务器，默认 http://localhost:5173/app/
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
python ./server.py     # Flask 从 dist 提供 /app/
```

未执行过 `npm run build` 时，`/app/` 会返回 503 并说明需要构建；`/` 和 `/api/*`
不受影响。

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
