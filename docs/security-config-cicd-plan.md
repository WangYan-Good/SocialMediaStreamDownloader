# Security, Configuration, and CI/CD Plan

更新时间：2026-06-11

## 1. 安全问题与修复方案

### P0：已提交凭据泄露

现象：

- `config/douyin/headers.yml` 曾包含完整 Cookie。
- `config/douyin/login.yml`、`config/douyin/post.yml`、`config/douyin/live.yml` 曾包含真实 `msToken`。
- `config/base_config.yml` 曾包含默认数据库账号密码 `admin/admin`。
- 代码示例中也出现过 Cookie / token 形态文本。

已做：

- 版本化配置改为 `${ENV_VAR:-default}` 占位符。
- `backend/src/library/baselib.py` 的 `load_yml()` 支持自动加载 `.env` 并递归替换环境变量。
- `backend/src/base/login.py`、`backend/src/platform/douyin/douyin_post_config.py` 切到统一 `load_yml()`。

仍需立即执行：

- 轮换所有曾经提交过的抖音 Cookie、`msToken`、数据库账号密码。
- 使用 `gitleaks` 或 `git filter-repo` 清理 Git 历史中的旧凭据；清理历史会影响协作者，需要统一窗口操作。
- 在仓库保护规则中强制启用 secret scanning，禁止含凭据的 PR 合并。

### P0：外部请求入口缺少访问控制

现象：

- `POST /` 会启动下载任务，原先无鉴权。

已做：

- `server.py` 增加可选 `SMSD_API_TOKEN`。配置真实 token 后，请求必须带 `Authorization: Bearer <token>` 或 `X-SMSD-Token`。

建议：

- 生产环境必须设置 `SMSD_API_TOKEN`。
- 若后续开放公网，改为用户登录 + RBAC + 任务所有者隔离。

### P0：SSRF 与滥用风险

现象：

- 前端提交 URL，后端会请求该 URL 并继续访问跳转后的地址。
- 原始校验只判断 `http://` / `https://`。

已做：

- `server.py` 增加 URL 长度、数量、scheme、域名白名单校验。
- 默认白名单为 `douyin.com,iesdouyin.com,v.douyin.com,live.douyin.com,www.douyin.com`。

建议：

- 对跳转后的最终 URL 也做白名单校验。
- 明确禁止内网 IP、localhost、metadata 地址和非标准端口。
- 为外部请求设置统一超时、重试上限和最大响应体大小。

### P1：SQL 注入风险

现象：

- 新的 `SocialMediaStreamDataTable` 已有参数化能力。
- 旧的 `backend/src/database/table/share_url.py` 仍存在多处 `.format()` 拼 SQL。

方案：

- 第一阶段：把 `share_url.py` 中所有用户/API 可控字段改为 `cursor.execute(sql, params)`。
- 第二阶段：所有表类继承并复用 `SocialMediaStreamDataTable` 的 `_quote_identifier()`、`insert_record()`、`get_record()`、`update_record()`。
- 第三阶段：CI 中加入 Bandit 与最小 SQL 拼接规则检查，禁止新增 `cursor.execute(f"...")` 和 `cursor.execute("...{}".format(...))`。

### P1：日志泄露风险

现象：

- 下载器会记录请求 header、stream URL、share URL、异常上下文。
- header 中可能包含 Cookie。

方案：

- 建立 `redact_sensitive()` 工具，对 `cookie`、`authorization`、`token`、`password`、`sessionid`、`msToken` 等键和值脱敏。
- 所有日志输出前统一通过脱敏函数。
- `save_response`、`save_error_response` 默认关闭；生产只允许临时开启，并限制保存路径、保留天数和访问权限。

### P1：Docker 默认部署风险

已做：

- Compose 不再提供弱密码默认值，密码缺失时直接失败。
- MySQL 端口默认只绑定 `127.0.0.1`。
- App 容器增加 `no-new-privileges:true` 和 `cap_drop: ALL`。
- Dockerfile 运行时不再执行 `run-server.sh` 联网安装依赖。

建议：

- 生产环境使用反向代理终止 TLS。
- MySQL 不对公网开放。
- 使用 Docker secrets 或部署平台 secret store 注入敏感配置。

### P2：依赖供应链风险

已做：

- `requirements.txt` 中宽松版本收紧为固定版本。
- CI 增加 `pip-audit`。

建议：

- 后续引入 `requirements.in` + `pip-compile --generate-hashes`。
- 为基础镜像启用定期重建与镜像漏洞扫描。

## 2. 统一配置按层级控制

推荐层级：

1. 代码默认值：只允许非敏感、安全默认值。
2. 版本化 YAML：保存业务结构和非敏感默认值，使用 `${VAR:-default}`。
3. `.env`：本地开发私有配置，不提交。
4. 容器/CI 环境变量：部署环境注入。
5. Secret store：生产凭据最终来源，例如 GitHub Actions Secrets、Docker secrets、Vault、云厂商 Secret Manager。

命名约定：

- 项目应用配置统一使用 `SMSD_*`。
- 平台凭据使用平台前缀，例如 `DOUYIN_*`。
- MySQL 容器初始化变量保留官方 `MYSQL_*`。

关键变量：

- `SMSD_DB_ENABLE`
- `SMSD_DB_HOST`
- `SMSD_DB_PORT`
- `SMSD_DB_NAME`
- `SMSD_DB_USER`
- `SMSD_DB_PASSWORD`
- `SMSD_DOWNLOAD_SAVE_PATH`
- `SMSD_DOWNLOAD_MAX_THREAD`
- `SMSD_API_TOKEN`
- `SMSD_ALLOWED_DOMAINS`
- `SMSD_MAX_URLS_PER_REQUEST`
- `DOUYIN_COOKIE_*`
- `DOUYIN_MSTOKEN`

控制原则：

- 越上层越具体，越下层越通用。
- 生产环境不得依赖仓库默认凭据。
- 配置加载只能有一个入口，即 `load_yml()`。
- 新增平台配置必须先进入 `.env.example` 和 `.env.docker.example`。

## 3. CI/CD 部署与检查

已新增 `.github/workflows/ci.yml`，包含：

- Python 3.12 环境校验。
- 依赖安装。
- `compileall` 语法检查。
- YAML 配置解析检查。
- pytest 自动执行；未收集到测试时不误报。
- `gitleaks` secret 扫描。
- `bandit` 静态安全分析。
- `pip-audit` 依赖漏洞扫描。
- `docker compose config` 校验。
- Docker 镜像构建。
- 非 PR 事件发布镜像到 GHCR。

推荐分支规则：

- PR 必须通过 `validate`、`security`、`docker`。
- 禁止直接 push 到 `main`。
- `main` 通过后发布 `ghcr.io/<owner>/<repo>:<sha>` 和分支 tag。
- 版本发布使用 `v*` tag。

推荐部署流程：

1. 合并到 `main` 后 CI 构建并推送镜像。
2. 目标服务器拉取指定 SHA 镜像。
3. 服务器通过 `.env` 或 secrets 注入配置。
4. 执行 `docker compose pull && docker compose up -d`。
5. 部署后检查健康状态、日志脱敏、下载目录权限和 MySQL 连接。

## 4. 后续路线图

短期：

- 轮换所有泄露凭据。
- 清理 Git 历史。
- 给生产环境设置 `SMSD_API_TOKEN`。
- 将 `share_url.py` 改为参数化 SQL。
- 日志脱敏。

中期：

- 引入任务队列，替代进程内线程直接执行下载。
- 添加任务状态表和查询接口。
- 对跳转最终 URL 做白名单与内网地址拦截。
- 将配置 schema 化，启动时校验必填项。

长期：

- 引入 Secret Manager。
- 做用户认证、权限、审计日志。
- 建立 release、rollback、镜像签名和 SBOM。
