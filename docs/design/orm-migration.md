# ORM 与数据库版本迁移设计

## 1. 目标

在不切换现有业务数据库访问逻辑的前提下，引入 SQLAlchemy ORM 模型与
Alembic schema migration，使数据库结构具备可追踪、可校验、可升级和可降级的版本历史。

首阶段目标：

- 使用 SQLAlchemy Declarative Models 描述当前生产运行使用的全部表。
- 使用 Alembic 管理基线版本及后续 schema revision。
- 新数据库可通过 `upgrade head` 创建完整结构。
- 已有数据库只有在严格 schema 校验通过后才能执行 `stamp` 纳管。
- 服务运行时检查迁移版本，数据库异常不阻断 live 获取与下载链路。
- 保留现有 PyMySQL、DBUtils、表类接口和业务 CRUD 行为。

首阶段不包含：

- 不将现有业务 CRUD 一次性切换到 SQLAlchemy Session。
- 不替换现有 DBUtils 连接池。
- 不转换 `backend/src/unit_test/database/migration/v1/` 中的旧版快照表。
- 不自动修改未通过校验的已有数据库。
- 不在服务启动时自动执行 schema migration。

## 2. 当前问题

当前运行时通过 PyMySQL 和 DBUtils 访问 MySQL。表结构、建表 SQL 和 CRUD 分散在
`backend/src/database/table/` 的多个类中。现有
`backend/src/unit_test/database/migration/` 主要承担旧数据搬运，不是版本化的 schema
migration，无法稳定回答数据库当前版本、目标版本及版本间变更内容。

因此后续新增字段、索引或约束时，代码定义、实际数据库结构和文档容易发生漂移。

## 3. 总体架构

```text
config/config.yml
        │
        ├── 现有 PyMySQL + DBUtils ── 现有业务 CRUD
        │
        └── SQLAlchemy Engine
                 ├── ORM Models / Metadata
                 ├── Alembic migrations
                 └── schema/version checker
```

建议目录：

```text
backend/src/database/
├── orm/
│   ├── base.py
│   ├── engine.py
│   └── models/
├── migration/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── migration_cli.py
├── migration_service.py
└── schema_guard.py
```

组件职责：

- `orm/base.py`：提供 Declarative Base 和稳定的约束命名约定。
- `orm/engine.py`：从统一 YAML 创建 SQLAlchemy Engine，不保存第二份数据库配置。
- `orm/models/`：定义全部生产表及其字段、索引和约束。
- `migration/env.py`：将 `Base.metadata` 提供给 Alembic。
- `migration/versions/`：保存基线及后续 revision。
- `migration_service.py`：封装版本读取、schema 比较、stamp、upgrade 和 downgrade。
- `migration_cli.py`：提供稳定的项目命令入口和退出码。
- `schema_guard.py`：管理运行时数据库 schema 状态，不执行业务 SQL。

SQLAlchemy Engine 使用与现有运行时相同的 PyMySQL 驱动。连接信息通过
`sqlalchemy.engine.URL.create()` 从 `config/config.yml` 构建，避免包含特殊字符的密码被
错误解析，也不把完整连接 URL 写入配置或日志。

`Base.metadata` 是新的生产 schema 定义来源。未来结构变化必须同时提交 ORM Model 和
Alembic revision。Alembic autogenerate 只生成候选 migration，生成结果必须人工审查。

现有表类中的建表 SQL 首阶段只为旧测试和离线兼容工具保留，不再作为生产运行时的自动建表
入口。生产持久化发现缺表或结构漂移时必须进入 `blocked`，提示执行显式迁移；不得通过
`CREATE TABLE IF NOT EXISTS` 绕过 Alembic。该限制只收回 schema 管理职责，不改变现有
CRUD 方法的输入、输出和查询语义。

## 4. 配置与依赖边界

- `config/config.yml` 继续作为唯一持久配置源。
- 不新增 `.env`、`alembic.ini` 密码或第二份数据库配置。
- Alembic 运行时通过项目代码注入 Engine，不从命令行传递凭据。
- 首阶段 SQLAlchemy Engine 只供模型、迁移、校验与未来 Session 工厂使用。
- 现有 PyMySQL/DBUtils 连接和业务 CRUD 继续工作，不与 SQLAlchemy Session 混用事务。
- 旧版 v1 数据迁移代码保持快照身份，不导入 ORM Model，也不参与 Alembic metadata。

## 5. 基线接入流程

项目命令统一通过以下入口执行：

```bash
python -m backend.src.database.migration_cli status
python -m backend.src.database.migration_cli check
python -m backend.src.database.migration_cli stamp
python -m backend.src.database.migration_cli upgrade
python -m backend.src.database.migration_cli downgrade REVISION --confirm-database DATABASE_NAME
python -m backend.src.database.migration_cli revision "change description"
```

服务启动不会隐式调用其中任何写命令。

### 5.1 新数据库

```text
读取统一 YAML
→ 创建 SQLAlchemy Engine
→ Alembic upgrade head
→ 执行基线 revision
→ 创建全部生产表
→ 写入 alembic_version
→ schema 校验
```

基线 revision 的 `upgrade()` 创建全部生产表。服务在执行前检查数据库必须未版本化且不含
任何受管表；已有库必须改走 `check + stamp`，避免 Alembic 创建部分表后才因重名失败。
执行降级前会先解析 Alembic 的实际 revision 步骤。只要路径将执行基线 downgrade（包括
`base`、`-1` 等等价目标），就只允许通过显式数据库名 override 创建且名称匹配
`smsd_migration_test_<12 位十六进制>` 的临时测试库；配置文件中的数据库即使碰巧匹配该
名称或提供确认参数也会被拒绝。

### 5.2 已有数据库

```text
读取统一 YAML
→ 确认数据库尚未被 Alembic 管理
→ 反射现有数据库结构
→ 与 Base.metadata 严格比较
→ 校验通过后 stamp head
→ 只写 alembic_version，不执行建表或 ALTER
```

`stamp` 是项目级安全命令，不提供绕过 schema 校验的快捷参数。已有数据库校验失败时只
报告差异，不自动修复、不自动建表，也不写入 Alembic 版本号。

## 6. Schema 校验规则

严格比较所有 ORM 管理表的：

- 表是否存在。
- 字段集合、字段类型及长度。
- nullable 和 server default。
- 主键、外键和唯一约束。
- 索引列、顺序和唯一性。
- MySQL 存储引擎、字符集和排序规则。

比较规则：

- 字段在物理表中的排列顺序不作为差异。
- `alembic_version` 不参与业务 schema 比较。
- ORM 未管理的旧表或外部表作为警告报告，不阻止纳管。
- ORM 管理表中的额外字段、索引或约束属于差异，阻止 `stamp`。
- Alembic autogenerate 只扫描 ORM 管理表，不生成删除遗留表的操作。
- 多个 Alembic heads 被视为非法状态。

Alembic 官方说明 autogenerate 不能可靠识别所有重命名、匿名约束和特殊类型变化，因此每个
候选 revision 都必须人工审查：
[Alembic Autogenerate](https://alembic.sqlalchemy.org/en/latest/autogenerate.html)。

## 7. 迁移命令

统一入口：

```bash
python -m backend.src.database.migration_cli status
python -m backend.src.database.migration_cli check
python -m backend.src.database.migration_cli stamp
python -m backend.src.database.migration_cli upgrade
python -m backend.src.database.migration_cli downgrade <revision> --confirm-database <database_name>
python -m backend.src.database.migration_cli revision "description"
```

命令语义：

- `status`：显示数据库 current revision、代码 head 和 Guard 状态。
- `check`：严格比较已有 schema 与 ORM Metadata，不写数据库。
- `stamp`：只有完整校验通过后才标记当前唯一 head。
- `upgrade`：默认升级到 `head`；未版本化但已含受管表时拒绝执行。
- `downgrade`：必须显式指定目标 revision；非临时库还必须以实际库名确认，且任何会执行
  基线 downgrade 的目标或相对目标都禁止用于生产库。
- `revision`：生成 autogenerate 候选文件，不自动执行 migration。

未来结构变更流程：

```text
修改 ORM Model
→ 生成候选 revision
→ 人工审查
→ 空库 upgrade 测试
→ 基线库 upgrade 测试
→ downgrade/upgrade 往返测试
→ 提交模型与 revision
```

## 8. 运行时 Schema Guard

`DatabaseSchemaGuard` 使用三个进程级状态：

- `ready`：数据库可达、current revision 等于唯一 head，且受管 schema 校验通过，允许持久化。
- `unavailable`：数据库当前不可达，按退避策略重新检查。
- `blocked`：数据库可达但没有版本、版本落后、超前、分叉或受管 schema 漂移，拒绝持久化。

启动及恢复流程：

```text
database.enable = false
→ 跳过数据库连接与迁移检查

database.enable = true
├── 数据库可达、revision = head 且受管 schema 正确
│   → ready，允许持久化
├── 数据库可达但 revision 不匹配或受管 schema 漂移
│   → blocked，live 获取与下载继续，持久化被拒绝
└── 数据库不可达
    → unavailable，live 获取与下载继续
    → 后续首次持久化前重新连接并检查 revision
```

Guard 只负责版本、受管 schema 与可用性判断。现有数据库构造和持久化入口在获取连接前检查
Guard。完整 schema 校验在启动、数据库恢复和迁移完成后的首次检查中执行，不在每条 SQL 前
重复反射全部表。数据库恢复且 revision 与 schema 均正确后自动切换到 `ready`；`blocked`
不自动执行迁移，只有显式执行 `upgrade` 或通过校验的 `stamp` 后才可能恢复。

生产运行路径不再自动创建缺失表。缺表是 schema 漂移，持久化被阻止，但 live 获取与下载
继续执行。

相同错误只在状态变化或退避周期到期时记录，避免每个下载任务重复输出相同日志。

## 9. 错误处理与安全

- 配置非法：命令退出码非 0，不回显配置内容。
- 数据库不可达：命令退出码非 0，只输出主机、端口和数据库名。
- schema 不一致：按表分组输出差异，不执行 `stamp`。
- current revision 落后、超前、缺失、分叉或受管 schema 漂移：Guard 进入 `blocked`。
- migration 执行失败：不伪造版本号，不自动 `stamp`。
- 代码或数据库存在多个 heads：`status` 稳定报告分叉，`upgrade` 和运行时 Guard 均拒绝继续。
- 密码、Cookie、Token 和完整数据库 URL 不进入日志、命令行或版本库。
- MySQL DDL 不承诺整体事务回滚。每个 revision 必须步骤明确、可诊断，并在破坏性变更前
  要求备份。

## 10. 测试设计

### 10.1 单元测试

- YAML 数据库配置到 SQLAlchemy `URL` 的映射。
- 密码包含特殊字符时能够正确连接且不泄露日志。
- ORM Metadata 包含全部生产表。
- 表、字段、主键、外键、索引和命名约定符合预期。
- CLI 参数、退出码与错误信息。
- Guard 的 `ready`、`unavailable`、`blocked` 状态转换。
- 数据库不可达或版本不匹配时 live 链路继续、持久化被阻止。
- 旧版 v1 快照不会被加载到 ORM Metadata。

### 10.2 真实 MySQL 集成测试

集成测试只能操作名称符合 `smsd_migration_test_<随机值>` 的临时数据库。创建和删除前都必须
校验前缀；任何不符合规则的数据库名立即拒绝。清理操作放在 `finally` 中，且永远不以
`config/config.yml` 中的生产数据库名作为删除目标。

测试覆盖：

- 空数据库 `upgrade head` 后生成完整 schema。
- 生成结构与 ORM Metadata 严格一致。
- `downgrade base → upgrade head` 往返成功。
- 已有数据库写入代表性数据后执行 `check + stamp`，数据和业务 schema 不变。
- 字段类型、nullable、默认值、AUTO_INCREMENT、列/表字符集与 collation、索引和约束差异
  均能阻止 `stamp`。
- 额外遗留表只产生警告，不被删除。
- 落后、超前、多 head 和无版本状态均能被识别。
- 未版本化但已有受管表时，`upgrade` 在执行任何 DDL 前拒绝。
- autogenerate 检查不会为非受管表生成删除操作。

### 10.3 现有链路回归

- 现有单元测试继续通过。
- PyMySQL/DBUtils CRUD 行为保持不变。
- live test mode 仍只跳过最终直播流数据传输。
- 数据库不可用时继续执行网络解析和下载。
- 数据库恢复且 revision 正确后持久化恢复。
- revision 不正确或受管 schema 漂移时不执行任何写入 SQL。
- 生产运行路径不能通过现有表类绕过 Alembic 自动建表。

## 11. 验收标准

- 新数据库可通过一条 `upgrade` 命令初始化。
- 已有数据库只有严格校验通过后才能安全纳管。
- ORM Model 与 Alembic revision 成为后续 schema 变更的唯一入口。
- 首阶段不改变现有业务查询结果和数据库数据。
- 服务在数据库不可达时保持 live 链路降级运行。
- schema 版本不匹配或实际结构漂移时不执行持久化。
- 测试不对现有生产数据库执行 DDL 或写入。
- 所有凭据不进入 Alembic 配置、命令行、日志或版本库。

## 12. 参考资料

- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/20/orm/)
- [SQLAlchemy Engine 与 URL](https://docs.sqlalchemy.org/en/20/core/engines.html)
- [Alembic Autogenerate](https://alembic.sqlalchemy.org/en/latest/autogenerate.html)
- [Alembic Commands API](https://alembic.sqlalchemy.org/en/latest/api/commands.html)
