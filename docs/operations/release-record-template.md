# Release Record Template

```text
release_identifier: RELEASE_TAG
source_commit_sha: 40_CHAR_DEVELOP_COMMIT
source_tree_sha: 40_CHAR_GIT_TREE
ci_run_id: GITHUB_ACTIONS_RUN_ID
ci_run_attempt: GITHUB_ACTIONS_RUN_ATTEMPT
tested_image_id: sha256:LOCAL_CONFIG_DIGEST
promotion_digest: ghcr.io/OWNER/REPOSITORY@sha256:REGISTRY_MANIFEST_DIGEST
requirements_sha256: REQUIREMENTS_LOCK_SHA256
python_base_digest: sha256:PYTHON_INDEX_DIGEST
node_base_digest: sha256:NODE_INDEX_DIGEST
mysql_digest: sha256:MYSQL_INDEX_DIGEST
pre_schema_revision: PRE_SCHEMA_REVISION
post_schema_revision: POST_SCHEMA_REVISION
backup_path: BACKUP_DIR
backup_checksums: SHA256SUMS_REFERENCE
upgrade_started_at: UTC_TIMESTAMP
upgrade_finished_at: UTC_TIMESTAMP
postcheck_result: PASS_OR_FAIL
postcheck_image_identity: PASS_OR_FAIL
```

External-host topology 另外记录：

```text
topology: external-host
publish_address: HOST_PUBLISH_ADDRESS
media_root: HOST_MEDIA_ROOT
media_snapshot_path: SNAPSHOT_PATH
media_snapshot_entries: ENTRY_COUNT
writer_authority_confirmed: PASS_OR_FAIL
db_privilege_verdict: sufficient_OR_insufficient
db_privilege_findings: HARDENING_FINDINGS_OR_NONE
application_uid_gid: UID:GID
userns_mapping: keep-id:uid=UID,gid=GID
media_write_proof: PASS_OR_FAIL
restore_drill_result: PASS_OR_FAIL
restore_drill_postcheck: PASS_OR_FAIL
migration_rehearsal_runs: RUN_COUNT
migration_rehearsal_invariants: PASS_OR_FAIL
```

`application_uid_gid` 与 `userns_mapping` 记录 application 进程的真实身份与它的映射。两者是
同一件事的两面：没有映射时，容器里的 application 对 operator 拥有的媒体树得到 `EACCES`，
而以 container root 做的写入测试会通过并且什么也没证明。`media_write_proof` 是以该身份
（不是以 entrypoint 的身份）完成 read/create/write/fsync/rename/unlink 以及 recovery journal
与 orphan quarantine 写入的结果。

`migration_rehearsal_runs` 至少为 2：同一个经 sha256 校验的 snapshot，两台全新 disposable
server，各自 0002 → head。`migration_rehearsal_invariants` 是精确 `COUNT(*)` 与主键校验和的
比较结果，不是 `table_rows` 估计值。

media snapshot 是同文件系统 reflink clone：它是 logical-loss rollback authority，不是
device-loss 保护。

Release record 禁止保存 registry credential、password、Cookie、session/CSRF token、root secret
或 platform token。
