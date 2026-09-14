# Release Operations Runbook

本 runbook 覆盖两种 deployment topology，两者并存且互不替代：

- **Compose deployment**：app + bundled MySQL + named `download_data` volume。开发、CI 与
  disposable restore drill 使用这一种。
- **External-host deployment**：exact-digest application container + 既有 host MySQL +
  bind-mounted host media tree。生产使用这一种。

两者的 backup、restore、rollback 与 postcheck 语义不同，下文分别说明；凡未标注的段落同时适用。
本 runbook 不替代环境自己的变更审批、加密 secret escrow 或 off-host backup policy。

> 本文档描述 tooling 支持的能力。它**不**表示生产 cutover 已经发生。

## Immutable tested artifact deployment

正式发布的 artifact authority 是成功的 **develop push CI**，不是生产机上的 Git checkout。
`Docker build and runtime smoke` 对 `smsd:ci` 完成全部 runtime、原始 Compose 与 restore drill
后，才把同一个 image 导出；独立 promotion job 校验 archive、source commit/tree、
`requirements.txt` SHA-256、loaded image ID 和 OCI labels，再推送 GHCR、按 registry digest
拉回并验证 image ID。operator 必须从该 run 的 promotion manifest 取得
`ghcr.io/OWNER/REPOSITORY@sha256:<64-hex>`，tag 仅用于 CI push transport，不是生产 authority。

固定 release procedure：

1. freeze `develop` source commit SHA，并确认四个 required jobs 与 promotion job 全部成功；
2. 保存 promotion manifest，核对 source tree、tested image ID、requirements SHA 与 CI run ID；
3. 执行 pre-release backup，并运行 `migration_cli status` / `migration_cli check`；
4. 用 canonical digest 部署：

   ```shell
   scripts/release_deploy.sh \
     --image ghcr.io/OWNER/REPOSITORY@sha256:<64-hex> \
     --expected-revision <40-char-develop-commit> \
     --project-name COMPOSE_PROJECT \
     --health-url HEALTH_URL
   ```

5. wrapper 先 pull exact digest，校验 revision/requirements labels，再以 `up -d --no-build`
   启动；postcheck 必须证明 running image ID 等于 promoted tested image ID，并核对固定 MySQL
   image reference；
6. 完成 authentication、task、media smoke；任一 identity、schema、health 或功能检查失败即
   触发 rollback/restore 决策。

生产服务器不得从 Git checkout 重新 docker build，也不得使用 `latest`、`sha-*` 或其他
tag-only reference。`run-docker.sh` 的 local build 能力只服务开发和 disposable restore drill。

## Recoverable state


Correctness-critical state 是 MySQL logical contents 与完整 media storage root。后者同时包含
媒体、隐藏目录 `.smsd-recording-recovery/`（journal 与 scan cursor）以及
`.smsd-recording-orphan-quarantine/`（已被 operator 隔离、尚未处置的媒体与其 record）。三者
必须作为一个单元捕获：只恢复媒体而不恢复 journal，启动后 recovery 会认为没有中断过；只恢复
媒体而不恢复 quarantine，则 operator 先前的隔离决定会消失，而该媒体在 catalogue 中仍无引用。

Compose topology 捕获为 `downloads.tar`；external-host topology 捕获为同一 storage root 的
reflink snapshot（见下）。`log_data` 只包含诊断日志，可另行归档，不属于 correctness-critical restore state。

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

## External-host deployment

生产 topology：exact-digest application container + 既有 host MySQL + bind-mounted host media
tree。它**不**迁移数据库，也**不**迁移媒体；唯一改变的是 application 本身成为容器。

### 前置条件（全部 fail closed）

1. **Operator stop/start authority。** 现有 writer 是 bare-metal process，没有 service
   manager。cutover 之后的每一步都假设它能被放回去，因此必须先写下 writer authority record
   （revision、start command、working directory、interpreter、stop/start procedure），并把
   `operator_confirmed_stop_start_authority` 明确置为 `true`：

   ```shell
   scripts/release_external_preflight.sh --writer-authority PATH
   ```

   P19 不安装 service manager —— 那属于独立授权的 host 变更。

2. **配置文件权限。** `config/config.yml` 含 database password，必须为 `0600` regular file。
   deployment 只拒绝，不代为 `chmod`：修改 operator 文件的权限是 operator 的决定。

3. **数据库权限。** 只读核对，不修改任何 grant：

   ```shell
   scripts/release_db_privileges.py --database NAME --grants-file PATH
   ```

   缺少权限是 release blocker；权限过宽（`*.*`、`WITH GRANT OPTION`）报告为
   `SECURITY HARDENING REQUIRED`，不阻塞本次 release，因为它先于本次 release 存在。

4. **Single writer。** deployment 会拒绝同名 container 已存在、或目标端口仍在服务。任何时刻
   只允许一个 writer 写同一个 database 与同一棵 media tree。

### 部署

```shell
scripts/release_external_deploy.sh   --image ghcr.io/OWNER/REPOSITORY@sha256:<64-hex>   --expected-revision <40-char-develop-commit>   --container-name CONTAINER   --config-file /path/to/config.yml   --media-root /path/to/media   --db-host HOST_ADDRESS_REACHABLE_FROM_CONTAINER   --port PORT   --publish-address PUBLISH_ADDRESS   --health-url HEALTH_URL   [--memory SIZE]
```

要点：

- **`--publish-address` 必须显式给出。** 容器内应用监听 `0.0.0.0`（否则 namespace 外无法到
  达）；host 暴露范围是另一件事，也是真正决定谁能访问生产的那件事，因此不设默认值。保持当前
  生产暴露范围即传入 `0.0.0.0`；收紧暴露是独立决定，不应与 cutover 捆绑。
- **不使用 `--network=host`。** 使用 bridge + 显式 host DB 地址：host networking 是靠取消
  namespace 边界来连通数据库，并且会把容器打开的每个端口都暴露出去。
- **不传 `--cpus`。** 本机 rootless user slice 只委派 `memory` 与 `pids`，未委派 `cpu`，
  CPU limit 无法生效。传入 `--cpus` 会被**拒绝**而不是被忽略——否则 operator 会以为限制生效。
  external-host mode 的既定策略是只设 memory limit、不设 CPU limit，与它所替代的 bare-metal
  application 一致。
- **canonical config 不被改写。** 容器通过一个非 secret 的环境值 `SMSD_DB_HOST` 得到可用的
  数据库地址，entrypoint 据此 stage 一份 `0600` 私有副本；password 始终只在挂载的配置文件里，
  不进入 argv、不进入环境、不进入日志。旧 bare-metal writer 直到被停止为止，读到的仍是原文件。
- **媒体按原路径 bind mount**（`/path:/path`），因此数据库里已有的路径无需转换。挂载的是
  storage root 而不是 recording 子树，否则 journal 与 quarantine 会留在容器内。

### Backup

```shell
scripts/release_external_backup.sh   --output BACKUP_DIR --config-file CONFIG --database NAME   --media-root MEDIA_ROOT --snapshot-root MEDIA_ROOT/.smsd-release-snapshot   --container-name CONTAINER --port PORT   --image DIGEST --db-host HOST --source-git-commit SHA
```

固定顺序：**停 writer → 证明已停 → dump → snapshot → manifest → checksums → verify**。

- writer 是否已停，同时检查 container 与端口：两者独立失效（容器可能已起但尚未监听；
  bare-metal writer 可能占着端口而没有任何容器）。engine 查询失败视为“状态未知”并拒绝，
  不视为“未运行”。
- credential 通过 `0600` option file 传递，`--defaults-extra-file` 必须是第一个参数；
  脚本在任何退出路径上都会删除它。
- dump 使用位置参数而非 `--databases`：`--databases X` 会在 dump 中写入 `CREATE DATABASE X`
  与 `USE X`，使 SQL 自行选择目标，restore 时的 `--database` 会被忽略。
- manifest 与 checksums 最后写入，因此任何捕获失败都会留下**无法通过 verify** 的 bundle。

### Media snapshot 与 rollback 边界

媒体以 XFS **reflink** clone 捕获，与源共享 extent，成本接近于零。它是同一文件系统上的
snapshot，因此：

- **覆盖**：逻辑损失——错误迁移、应用缺陷、误删。
- **不覆盖**：设备损失。`/dev/sdb1` 故障时 snapshot 一并丢失。设备级保护属于 off-host backup
  policy，不在本 release contract 内。

snapshot root 必须与 media root 同一文件系统（reflink 无法跨文件系统），因此它位于 media root
之内；必须是**隐藏目录**，否则 orphan scan 会把 snapshot 当作媒体遍历。snapshot 自身被排除在
clone 之外，否则每次 release 都会把上一次嵌套进去。

snapshot 记录的是**身份**（relative path、size、mtime_ns、device、inode）而非内容哈希：两 TB
的逐文件哈希会占满整个 cutover 窗口。这些 device/inode 用于证明 snapshot 对象未被替换，
**不**用于校验 restore 产物——clone 与 restore 必然产生新的 inode。

### Restore drill

只允许恢复到 disposable database 与 isolated media path：

```shell
scripts/release_external_restore_drill.sh   --backup BACKUP_DIR   --restore-database smsd_restore_test_NAME   --restore-media-root ISOLATED_PATH   --config-file DISPOSABLE_CONFIG
```

拒绝条件：database 名不符合 `smsd_restore_test_*`、与 source 相同、media root 是 live media
root 或位于其内部（按规范化路径比较）、目标目录已有内容。drill 只 clone snapshot，不移动它：
snapshot 是产出它的那次 release 的 rollback authority。restore 之后会核对目标 database 确实
有表——若 dump 再次自行选择目标，这会把静默成功变成失败。

## Rollback choices

External-host topology 的 rollback authority 由三部分组成，缺一不可：operator 对旧 writer 的
stop/start authority（见前置条件 1）、pre-release database bundle、以及 media reflink
snapshot。snapshot 只覆盖逻辑损失，不覆盖设备损失。

- **App-only rollback**：仅当旧 app 已证明兼容当前 schema，或该 release 没有 schema change。
- **Schema-changing rollback default**：previous application 加 pre-release full backup restore。
- **In-place downgrade**：仅限 advanced/manual path；exact migration downgrade code 已 review，
  disposable restored copy 已测试，显式 TARGET_REVISION 已批准，且 backup 已验证。

通用 release procedure 不推荐相对 downgrade。每次 release 记录 release tag、commit、image、
pre/post schema、backup path/checksums、开始/结束时间和 postcheck 结果，格式见
`release-record-template.md`。

## Post-upgrade verification

运行 `scripts/release_postcheck.sh --health-url HEALTH_URL`。Compose deployment 额外传
`--project-name COMPOSE_PROJECT`。正式发布由 `release_deploy.sh` 进一步传入 expected image、
revision、requirements SHA 与 MySQL digest；这些 identity、schema status、schema check、HTTP
health、app running 或 MySQL health 任一失败都必须返回 non-zero。restore drill 不使用 GHCR
artifact，因此 identity 参数保持 optional，原有 isolated restore contract 不变。

Compose deployment 还必须确认 app 与 MySQL 的 container-engine 日志限制实际进入运行容器，
而不只是存在于 YAML。对两个 container ID 分别检查：

```shell
docker inspect --format '{{.HostConfig.LogConfig.Type}}' CONTAINER_ID
docker inspect --format '{{index .HostConfig.LogConfig.Config "max-size"}}' CONTAINER_ID
docker inspect --format '{{index .HostConfig.LogConfig.Config "max-file"}}' CONTAINER_ID
```

期望依次为 `json-file`、`10m`、`5`。应用自己的 `server.log` 固定使用 10 MiB active file
与 9 个 backups，并把 file/console 的单条最终 UTF-8 record 限制在 64 KiB。升级前遗留的
dated rotated logs 不会自动删除；如需清理，operator 必须先审查，不应建立每日手工清理新日志的流程。

## Deployment credential lifecycle

`config.yml` 的 application DB password 与 `mysql-root-password` 是不同 credential。修改
`database.password` 不会修改 MySQL account；修改 root secret file 也不会 rotate 已初始化的
root account。正确 rotation 必须先在 MySQL 内更新账户，再原子更新对应 `0600` secret，验证
新 credential，最后撤销旧 credential；不能只改文件然后 restart。

应用账户使用 CLI-only lifecycle：`create-user`、`set-role`、`set-password`、`disable-user`、
`enable-user`、`revoke-sessions`。密码只能通过 getpass/confirm prompt 输入，不能通过 argv、
environment 或 stdout。password reset 与 disable 必须 revoke 该用户全部 sessions；enable 不得
恢复旧 session。
