# Release Operations Runbook

本 runbook 适用于当前单进程 Compose deployment。它不替代环境自己的变更审批、加密 secret
escrow 或 off-host backup policy。

## Recoverable state


Correctness-critical state 是 MySQL logical contents 与完整 `download_data`。后者同时包含媒体、
隐藏目录 `.smsd-recording-recovery/` 及 scan cursor，媒体与 journal 必须作为一个 archive
单元。`log_data` 只包含诊断日志，可另行归档，不属于 correctness-critical restore state。

普通 data bundle 不包含 plaintext deployment credentials、platform cookies、raw session
tokens、CSRF tokens 或 MySQL root secret。但是 `database.sql` 仍包含 sensitive application
data，包括 password hashes 与 session-token hashes，因此 entire backup bundle 必须作为
sensitive data 以 `0700` 目录和 `0600` 文件权限保存，并采用加密、off-host backup storage。
`config/config.yml` 与 `config/mysql-root-password` 仍应分别以 `0600` 权限存入独立 secret
escrow，不自动放入 data bundle。

## Backup and restore

一致性 backup 顺序固定为：停止 app writer、保持 MySQL 运行、以
`mysqldump --single-transaction` 创建 logical dump、归档完整 download volume、写 manifest 与
SHA-256 checksums，最后恢复 app 原先的运行状态。使用：

```shell
scripts/release_backup.sh --output BACKUP_DIR --project-name COMPOSE_PROJECT
```

恢复只允许到显式 fresh/isolated Compose project：

```shell
scripts/release_restore.sh --backup BACKUP_DIR \
  --project-name smsd-restore-test-UNIQUE \
  --health-url HEALTH_URL
```

restore 必须先校验 manifest/checksums，再建立 MySQL、恢复 logical SQL、恢复完整 downloads，
最后才启动 app 并执行 startup recovery 与 postcheck。禁止覆盖 live/default project；不要把
live `/var/lib/mysql` volume copy 当作默认 restore。

默认且唯一受支持的数据库路径是 logical restore，不支持把 raw mysql_data volume 当作
release restore。新隔离环境可以使用 new MySQL root secret；root secret 不属于 SQL data。
application DB account 仍由 canonical config.yml 初始化，其中 `database.name` 必须与
backup manifest 一致，否则 restore 在导入前拒绝。修改 application DB password 还必须先在
MySQL 内完成相应账户 rotation，不能只改配置文件。

## Rollback choices

- **App-only rollback**：仅当旧 app 已证明兼容当前 schema，或该 release 没有 schema change。
- **Schema-changing rollback default**：previous application 加 pre-release full backup restore。
- **In-place downgrade**：仅限 advanced/manual path；exact migration downgrade code 已 review，
  disposable restored copy 已测试，显式 TARGET_REVISION 已批准，且 backup 已验证。

通用 release procedure 不推荐相对 downgrade。每次 release 记录 release tag、commit、image、
pre/post schema、backup path/checksums、开始/结束时间和 postcheck 结果，格式见
`release-record-template.md`。

## Post-upgrade verification

运行 `scripts/release_postcheck.sh --health-url HEALTH_URL`。Compose deployment 额外传
`--project-name COMPOSE_PROJECT`。schema status、schema check、HTTP health、app running 或 MySQL
health 任一失败都必须返回 non-zero。

## Deployment credential lifecycle

`config.yml` 的 application DB password 与 `mysql-root-password` 是不同 credential。修改
`database.password` 不会修改 MySQL account；修改 root secret file 也不会 rotate 已初始化的
root account。正确 rotation 必须先在 MySQL 内更新账户，再原子更新对应 `0600` secret，验证
新 credential，最后撤销旧 credential；不能只改文件然后 restart。

应用账户使用 CLI-only lifecycle：`create-user`、`set-role`、`set-password`、`disable-user`、
`enable-user`、`revoke-sessions`。密码只能通过 getpass/confirm prompt 输入，不能通过 argv、
environment 或 stdout。password reset 与 disable 必须 revoke 该用户全部 sessions；enable 不得
恢复旧 session。
