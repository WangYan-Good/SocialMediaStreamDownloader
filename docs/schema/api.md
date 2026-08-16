# 1. 场景

- 下载直播
```text
```

- 浏览下载历史并检查主播当前是否正在直播
```text
GET  /api/history/owners            按条件筛选历史主播（纯数据库，不发网络请求）
POST /api/live/probe                对筛选结果发真实请求，判定此刻是否在播
GET  /api/live/probe/<batch_id>     轮询探测进度
POST /api/resolve + POST /api/tasks  对在播资源创建现代录制任务
```

筛选与判定是两件事：数据库只负责把历史主播缩到一页（默认上限 10 条），
真实直播状态只来自 `/api/live/probe` 的网络请求。`share_url` 上的
`last_live_status` / `last_checked_at` 是探测结果的缓存，用于筛选排序和
「上次见到在播」提示，**不是**当前是否在播的判据。

# 2. API 完整契约

<!-- INITIALIZED: v0.1 - 完整的 API 契约 -->

## 2.1 已退休的 root `POST /`

P16 已删除这个 Legacy raw-URL dispatcher endpoint；请求自然返回 `405 Method
Not Allowed`，没有重定向或替代 route。现代客户端先通过 `/api/resolve`（或
`/api/resolve/batch`）取得 receipt，再通过 `/api/tasks` 创建独立任务。

主播的 `favorite` / `score` 是 Creator Account 独立持久化属性，不属于任务创建
payload。多资源提交也不会创建 batch task；每个成功解析项继续使用自己的 receipt
创建普通任务。

## 2.2 `GET /api/history/owners`

按条件筛选历史下载过的主播。只读数据库，不发任何平台请求。

**Query Parameters:**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `q` | string | 否 | null | 昵称模糊搜索（`%` `_` `\` 已转义） |
| `platform` | string | 否 | `douyin` | 平台 |
| `favorite` | bool | 否 | false | 只看 `favorite_owner` 中有评分的主播 |
| `score_min` / `score_max` | integer | 否 | null | 评分区间，0-100 |
| `last_live_within` | enum | 否 | null | `1h` / `24h` / `7d` / `30d` / `never`（上次见到在播） |
| `user_status` | enum | 否 | null | `正常` / `已注销` |
| `sort` | enum | 否 | `last_checked_at` | `last_checked_at` / `actived_count` / `score` / `nickname` |
| `order` | enum | 否 | `desc` | `asc` / `desc`（`actived_count asc` = 下载次数最少，`last_checked_at asc` = 最久未下载） |
| `page` | integer | 否 | 1 | 页码，从 1 开始 |
| `page_size` | integer | 否 | `history.page_size_limit` | 超出配置上限时钳到上限，不报错 |

**Response 200:**
```json
{
  "status": "success",
  "code": 200,
  "data": {
    "total": 7538,
    "page": 1,
    "page_size": 10,
    "items": [
      {
        "owner_user_id": "1602429655200697",
        "nickname": "羔冷锅锅",
        "live_share_url": "https://v.douyin.com/xxxx/",
        "directory_name": "羔冷锅锅",
        "user_status": "正常",
        "actived_count": 29,
        "score": 60,
        "favorite": true,
        "last_live_status": 2,
        "last_checked_at": "2026-08-09T12:56:45.125",
        "last_room_id": "7671849893874502443"
      }
    ]
  }
}
```

`last_live_status`：2 = 直播中，4 = 已结束，null = 从未记录。配合 `last_checked_at`
读作「上次见到在播是什么时候」，不是「现在在播」。

**错误码:**

| HTTP Code | error.message |
|-----------|---------------|
| 400 | 筛选参数非法（如 `sort` 不在白名单内） |
| 503 | 历史功能需要启用数据库 / 数据库暂时不可用 |
| 500 | 服务器内部错误，请稍后重试 |

## 2.3 `GET /api/history/owners/<owner_user_id>/sessions`

展开某个主播的历史直播场次，最新在前。

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `limit` | integer | 否 | 20 | 上限 100 |
| `platform` | string | 否 | `douyin` | 平台 |

**Response 200:**
```json
{
  "status": "success",
  "code": 200,
  "data": {
    "items": [
      {
        "observed_at": "2026-08-09T12:56:45.125",
        "room_id": "7671849893874502443",
        "title": "哈喽",
        "room_status": 2,
        "start_time": null,
        "finish_time": null,
        "status_code": null
      }
    ]
  }
}
```

## 2.4 `POST /api/live/probe`

对一批主播发真实请求，判定此刻是否正在直播。**只判定，不下载。**

一次探测是 2 个平台请求加两段 1.5-4.5 秒的随机间隔，约 5-12 秒/主播，因此批量大小
受 `platform.douyin.live.probe.max_batch_size` 限制，并发受 `concurrency` 限制。
`cache_ttl_seconds` 内重复提交的主播直接返回缓存值，不再发请求。

**Request Body:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `owner_user_ids` | list | 是 | 主播 ID 数组，去重后不得超过 `max_batch_size` |

**Response 202:**
```json
{
  "status": "success",
  "code": 202,
  "data": {
    "batch_id": "0f3c…",
    "done": false,
    "items": [
      { "owner_user_id": "1", "state": "pending", "nickname": "羔冷锅锅",
        "live_share_url": "https://v.douyin.com/xxxx/", "cached": false }
    ]
  }
}
```

`state`：`pending` / `running` / `living` / `offline` / `error`。

**错误码:**

| HTTP Code | error.message |
|-----------|---------------|
| 400 | 请求必须是 JSON 格式 / 缺少必需字段 / 超过批量上限 |
| 503 | 历史功能需要启用数据库 |
| 500 | 服务器内部错误，请稍后重试 |

## 2.5 `GET /api/live/probe/<batch_id>`

轮询一个探测批次的进度。`done` 为 `true` 时可停止轮询。批次保留
`platform.douyin.live.probe.batch_retention_seconds` 秒后失效。

**Response 200:** 与 `POST /api/live/probe` 的 `data` 结构一致，
`items[].state` 会随探测推进变化，失败项带 `message`。

**错误码:**

| HTTP Code | error.message |
|-----------|---------------|
| 404 | 探测批次不存在或已过期 |
| 503 | 历史功能需要启用数据库 |

> 批次保存在进程内存中，仅适用于当前的单进程部署；换成多 worker 的 WSGI 需要替换
> `ProbeBatchStore` 的实现。
