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

Release record 禁止保存 registry credential、password、Cookie、session/CSRF token、root secret
或 platform token。
