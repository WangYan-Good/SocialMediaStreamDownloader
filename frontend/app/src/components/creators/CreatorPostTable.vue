<script setup lang="ts">
import { formatTaskTime } from '@/components/tasks/taskPresentation'
import { formatCount } from '@/components/creators/creatorPresentation'
import { isHttpUrl } from '@/utils/url'
import type { OwnerPost } from '@/types/owner'

defineProps<{ posts: OwnerPost[]; selectedAwemeIds: string[] }>()

defineEmits<{ toggle: [string] }>()

function publishedAt(createTime: number | null): string {
  if (createTime === null) {
    return '—'
  }
  return formatTaskTime(new Date(createTime * 1000).toISOString())
}

function durationLabel(duration: number | null): string {
  if (duration === null) {
    return '—'
  }
  const seconds = Math.round(duration / 1000)
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`
}

/** What this server already has of one post. */
function downloadLabel(post: OwnerPost): string {
  if (!post.downloaded) {
    //
    // Never "下载失败": nothing has been attempted. This is simply a post the
    // server does not have.
    //
    return '未下载'
  }
  if (
    post.saved_count !== null &&
    post.media_count !== null &&
    post.saved_count < post.media_count
  ) {
    return `部分 ${post.saved_count}/${post.media_count}`
  }
  return '已下载'
}
</script>

<template>
  <div class="table-scroll">
    <table class="table">
      <thead>
        <tr>
          <th scope="col"><span class="table__sr">选择</span></th>
          <th scope="col">封面</th>
          <th scope="col">文案</th>
          <th scope="col">类型</th>
          <th scope="col">时长</th>
          <th scope="col">发布时间</th>
          <th scope="col">点赞 / 评论</th>
          <th scope="col">下载状态</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="post in posts" :key="post.aweme_id">
          <td>
            <input
              type="checkbox"
              :checked="selectedAwemeIds.includes(post.aweme_id)"
              :aria-label="`选择作品 ${post.aweme_id}`"
              @change="$emit('toggle', post.aweme_id)"
            />
          </td>
          <td>
            <!--
              Only a plain http(s) url becomes an image source. A cover comes
              from a platform payload, and a `data:` or `javascript:` value
              there must not be loaded.
            -->
            <img
              v-if="isHttpUrl(post.cover_url)"
              class="table__cover"
              :src="post.cover_url"
              :alt="''"
              loading="lazy"
            />
            <span v-else class="table__cover table__cover--empty" aria-hidden="true"></span>
          </td>
          <td class="table__desc">{{ post.desc || '（无文案）' }}</td>
          <td>{{ post.aweme_type === 'image' ? '图文' : '视频' }}</td>
          <td>{{ durationLabel(post.duration) }}</td>
          <td class="table__muted">{{ publishedAt(post.create_time) }}</td>
          <td class="table__muted">
            {{ formatCount(post.digg_count) }} / {{ formatCount(post.comment_count) }}
          </td>
          <td>{{ downloadLabel(post) }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.table-scroll {
  overflow-x: auto;
}

.table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.table th,
.table td {
  padding: var(--space-2) var(--space-3);
  border-bottom: 1px solid var(--color-border);
  text-align: left;
  vertical-align: middle;
  white-space: nowrap;
}

.table th {
  color: var(--color-muted);
  font-size: 0.75rem;
  font-weight: 600;
}

.table__cover {
  display: block;
  width: 48px;
  height: 64px;
  object-fit: cover;
  border-radius: var(--radius-1);
  background: var(--color-background);
}

.table__cover--empty {
  border: 1px dashed var(--color-border);
}

.table__desc {
  max-width: 20rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.table__muted {
  color: var(--color-muted);
}

.table__sr {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip-path: inset(50%);
}
</style>
