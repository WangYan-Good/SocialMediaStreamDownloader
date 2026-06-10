# 1. 场景

- 下载直播
```text
```

# 2. API 完整契约

<!-- INITIALIZED: v0.1 - 完整的 API 契约 -->

## 2.1 `POST /`

**URL:** `POST /`
**权限:** TODO：已认证用户

**Query Parameters:**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `urls` | list | 是 | null | 逗号分隔的 living 分享 URL |
| `score` | integer | 否 | 0 | 对分享的 urls 的喜好程度，范围在0-100 |
| `favorite` | bool | 否 | false | `score` 的标记位，为 `true` 表明 `score` 有效 |

**Response 200:**
```json
{
  "status": "error",
  "message": "请求必须是 JSON 格式",
  "code": 400
}
```

**错误码:**

| HTTP Code | error.code | error.message |
|-----------|------------|---------------|
| 401(TODO) | `unauthorized` | 未认证或 token 无效 |
| 400 | `invalid_params` | 查询参数格式错误 |
| 500 | `internal_error` | 服务器内部错误 |

