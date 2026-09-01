# Database Migration Operations

本指南是当前 operator procedure。历史 migration revision 只用于审计历史，不能从历史文档
复制为当前 release 的 rollback target。

## Current head discovery

始终由代码与数据库共同报告版本：

```shell
python -m backend.src.database.migration_cli status
python -m backend.src.database.migration_cli check
```

`status` 输出 `state`、`current` 和 `heads`。当前 code head 是 `heads`，不得要求 operator
从 README 手工读取或猜测。`upgrade` 默认升级到当前 code head：

```shell
python -m backend.src.database.migration_cli upgrade
```

## Mandatory migration preflight

正式升级前必须完成并写入 release record：

1. 记录 application commit 与 immutable image ID/tag。
2. 执行 `migration_cli status`，记录 pre-upgrade revision、state、current、heads。
3. 执行 `migration_cli check` 并保存非敏感结果。
4. 使用 release backup helper 创建并验证 pre-upgrade backup。
5. 记录 target code/image 与经人工 review 的兼容性决定。

这里的 **pre-upgrade backup** 是硬 gate。`unversioned`、`multiple_heads`、`schema_drift`、
`ahead_or_unknown`、`diverged` 或其他 blocked 状态都禁止直接 upgrade；应先停止 release，
按现有 migration CLI contract 调查并人工处理。

## Mandatory post-upgrade gate

升级后必须再次执行：

```shell
python -m backend.src.database.migration_cli status
python -m backend.src.database.migration_cli check
```

post-upgrade gate 只在 `state=ready`、`current=head` 且 `migration_cli check` 报告
`managed schema is compatible` 时通过。随后还必须运行 `scripts/release_postcheck.sh` 验证
HTTP 与部署健康；任一步失败都停止 release。

## Explicit rollback target

In-place schema downgrade 是 advanced/manual path，不是默认 rollback。目标必须来自
release compatibility record 并经过逐 revision 人工 review：

```shell
TARGET_REVISION=<reviewed revision>
python -m backend.src.database.migration_cli downgrade \
  "$TARGET_REVISION" --confirm-database DATABASE_NAME
```

不要把“当前 head 的上一版”当作目标，也不要把相对 downgrade 当作通用建议。执行前必须有
已校验 backup，并先在 disposable restored copy 上演练 exact downgrade code。

## Existing unversioned database

`stamp` 只写版本表，不运行 DDL。仅在 schema 已人工识别且符合现有 CLI guard 时使用；对
非-head revision 必须显式提供该数据库的真实名称。不要把任何历史 revision 固化到当前
runbook。完成纳管后重新运行 status/check，再按 preflight 执行 upgrade。
