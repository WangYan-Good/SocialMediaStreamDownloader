# Release Record Template

```text
release_identifier: RELEASE_TAG
application_commit: GIT_COMMIT
application_image: RELEASE_IMAGE
pre_schema_revision: PRE_SCHEMA_REVISION
post_schema_revision: POST_SCHEMA_REVISION
backup_path: BACKUP_DIR
backup_checksums: SHA256SUMS_REFERENCE
upgrade_started_at: UTC_TIMESTAMP
upgrade_finished_at: UTC_TIMESTAMP
postcheck_result: PASS_OR_FAIL
```

Release record 禁止保存 password、Cookie、session/CSRF token、root secret 或 platform token。
