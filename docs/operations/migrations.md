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

## External-host topology

`migration_cli` 不接受 DSN，也不读环境变量：它总是读取 `<root>/config/config.yml`。因此针对
host MySQL 运行它的唯一方式，是在 disposable container 内挂载 canonical config 并提供
`SMSD_DB_HOST`——这正是 external backup 与 external postcheck 读取 schema state 的方式：

```shell
CONTAINER_ENGINE run --rm \
  --env SMSD_DB_HOST=HOST_ADDRESS \
  --volume /path/to/config.yml:/run/secrets/config.yml:ro \
  IMAGE_DIGEST \
  python -m backend.src.database.migration_cli status
```

`state=ready` 之外的任何结果都会让 external backup 拒绝继续：对 schema 状态未知的数据库所做的
dump，其 restore 语义同样未知。

## Migration rehearsal

Migration rehearsal 必须针对 production-shaped snapshot 在 disposable MySQL 上进行，
不得针对生产数据库执行 `upgrade`。

```shell
scripts/release_migration_rehearsal.sh \
  --snapshot PATH --expected-sha256 SHA256 --expected-source-revision REVISION
```

它证明的是三件不同的事，不要互相当替代品：

1. **数据没有丢。** 每张表取精确 `COUNT(*)`，另取主键的顺序无关指纹
   （`BIT_XOR(CRC32(pk))`）。**不使用** `information_schema.tables.table_rows`：那对 InnoDB
   是优化器从抽样索引页维护的估计值，会在无人控制的时刻重算，跨 upgrade 比较它会在没有变化处
   报出差异、在真的丢了行时报出一致。

   两者的强度不同，不要混为一谈。`COUNT(*)` 是**精确**值；`BIT_XOR(CRC32(pk))` 是
   **概率性指纹**——CRC32 只有 32 位，不同的主键集合可能碰撞，因此它不是数学意义上的
   identity。它只在**行数已经相等**时用来发现「行数没变但行被换掉了」，绝不替代行数本身。

   判定规则：**upgrade 之前就存在的表，行数必须完全相等**（多了也算失败），且主键指纹必须
   相同；upgrade 新建的表允许存在；唯一的例外是 `alembic_version`——它的那一行本来就该被
   upgrade 改写，所以允许 revision 前进，但不允许丢行、也不允许多出行。

   曾经的规则允许「行数变多」并只记一条 note，于是「删掉一千条旧行、插入两千条新行」会通过：
   行数更高，就再也不去看指纹了。那正是这套检查存在的意义所在的失败。将来若确有 migration
   合法地给既有表加行，正确做法不是恢复「允许增长」，而是为那一张表写明确的最小例外，并附上
   baseline 主键仍然存在的证明——「比以前多」从来不说明「原来的还在」。
2. **升级可重复。** 整个流程做两遍，每遍都从**同一个经过 sha256 校验的不可变 snapshot** 恢复到
   一台**全新**的 disposable server 上，各自证明 source revision、各自 upgrade 到 head、各自
   `status` 与 `check`，然后比较两遍的 invariants。
3. **升级幂等。** 在 head 上再跑一次 `upgrade` 是 no-op。这一条保留，但它**不能**替代第 2 条：
   「对 head 再执行一次」与「0002 → head 第二次执行」是两个不同的命题。

rehearsal 不改写工作副本的 `config/config.yml`。`migration_cli` 只认一个固定路径，所以 rehearsal
把项目复制一份到临时目录，在那份副本里写配置。snapshot 在两遍之前与之后各校验一次 sha256。
