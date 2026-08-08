# 配置与凭据安全

## 当前边界

- `config/config.yml` 是唯一持久运行时配置源。
- 真实配置被 Git 和 Docker 构建上下文排除，不得提交或复制到镜像。
- 应用容器只读挂载该文件到 `/run/secrets/config.yml`，不接收配置型环境变量。
- 容器入口以 root 校验配置并复制到可写层 `/app/config/config.yml`，设置为
  `appuser` 所有、权限 `0600` 后，通过 `initgroups/setgid/setuid` 降权执行服务。
- Docker Compose 必需的端口和 MySQL 初始化变量由 `run-docker.sh` 临时派生；
  临时文件权限为 `0600`，并在命令退出时删除。
- 缺失或非法配置会阻止本地与容器启动，错误只说明配置无效，不回显配置值。
- `download.test_mode` 不是安全隔离开关：它只跳过直播流数据传输，仍会访问平台网络接口
  和已启用的数据库。
- Alembic 不使用包含凭据的 `alembic.ini` 或 `sqlalchemy.url`；迁移 Engine 仅从统一 YAML
  在进程内构造，CLI 输出不会显示完整 URL 或密码。
- 服务启动只执行只读版本/schema 检查，不自动 `upgrade`、`stamp`、建表或删表。

## 初始化

```bash
mkdir -p config
cp docs/design/config.yml.example config/config.yml
chmod 600 config/config.yml
```

填写真实值后，本地使用 `sh ./run-server.sh`，容器使用
`./run-docker.sh up -d`。不要创建 `.env` 作为第二份配置。

## 凭据处理

- 使用最小权限的数据库账号。
- 定期轮换数据库密码、Cookie、Token 等凭据。
- 不在日志、测试 fixture、Issue、聊天记录或截图中粘贴真实值。
- `docs/design/config.yml.example` 只能保留脱敏占位符。

## 迁移安全

- 已有数据库必须先执行只读 `check`；只有严格兼容且尚未版本化时，`stamp` 才会写版本表。
- `upgrade`、`downgrade` 和生成的 revision 必须人工审查；任何可能删除或改写数据的迁移前
  必须完成可恢复备份。未版本化但已有受管表的数据库禁止直接 `upgrade`；非临时库降级
  必须用实际库名确认。任何会执行基线 downgrade 的目标（含 `base`、`-1` 等等价形式）
  只允许显式 override 且严格命名的临时迁移测试库，配置库名不能自动获得临时库身份。
- 真实 MySQL 集成测试只能创建匹配
  `^smsd_migration_test_[0-9a-f]{12}$` 的随机数据库，且在 `finally` 中删除；正式数据库名
  不能进入测试库删除逻辑。
- 非受管表只报告 warning，Alembic 自动生成、升级和降级均不得删除它们。

## 历史凭据

防止当前配置进入新镜像不等于撤销历史泄露。Git 历史中曾出现过的凭据应由维护者
在外部完成轮换；如需历史重写，必须单独协调所有协作者，本次配置迁移不执行该操作。
