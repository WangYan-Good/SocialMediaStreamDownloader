// Owner browse: profile + post list + download.
//
// Post payloads stay on the server.  This page holds only what it renders and
// sends aweme ids back, so a page of nineteen posts costs one small request
// rather than moving a megabyte of platform objects through the browser.
(function () {
  'use strict';

  var POLL_INTERVAL_MS = 1500;

  // Sharing from the app copies a sentence, not a bare link:
  //   0- 长按复制此条消息，打开抖音搜索，查看TA的更多作品。 https://v.douyin.com/xxx/ 4@1.com :0pm
  // Pull the link out rather than making the user edit the text down.  Trailing
  // punctuation is trimmed because Chinese full stops and brackets sit flush
  // against the url when it ends a sentence.
  var URL_PATTERN = /https?:\/\/[^\s]+/g;
  var TRAILING_NOISE = /[)\]}>,.;:!?，。；：！？、）】》]+$/;

  function extractUrl(text) {
    var matches = String(text || '').match(URL_PATTERN);
    if (!matches || !matches.length) { return ''; }
    return matches[0].replace(TRAILING_NOISE, '');
  }

  function OwnerPosts(root) {
    this.root = root;
    this.secUserId = null;
    this.nextCursor = 0;
    this.hasMore = false;
    this.loaded = 0;
    this.awemeCount = null;
    this.jobId = null;
    this.pollTimer = null;

    this.urlInput = root.querySelector('.op-url');
    this.status = root.querySelector('.op-status');
    this.card = root.querySelector('.op-owner-card');
    this.toolbar = root.querySelector('.op-toolbar');
    this.table = root.querySelector('.op-table');
    this.rows = root.querySelector('.op-rows');
    this.pager = root.querySelector('.op-pager');
    this.selectAll = root.querySelector('.op-select-all');
    this.selectionInfo = root.querySelector('.op-selection-info');
    this.downloadSelected = root.querySelector('.op-download-selected');
    this.downloadAll = root.querySelector('.op-download-all');
    this.jobStatus = root.querySelector('.op-job-status');
    this.pageInfo = root.querySelector('.op-page-info');

    this.bind();
  }

  OwnerPosts.prototype.bind = function () {
    var self = this;
    this.root.querySelector('.op-read').addEventListener('click', function () {
      self.read();
    });
    this.urlInput.addEventListener('keydown', function (event) {
      if (event.key === 'Enter') { self.read(); }
    });
    this.root.querySelector('.op-load-more').addEventListener('click', function () {
      self.loadMore();
    });
    this.selectAll.addEventListener('change', function () {
      Array.prototype.forEach.call(
        self.rows.querySelectorAll('.op-row-select'),
        function (box) { box.checked = self.selectAll.checked; }
      );
      self.refreshSelection();
    });
    this.downloadSelected.addEventListener('click', function () {
      self.startDownload({ aweme_ids: self.selectedIds() });
    });
    this.downloadAll.addEventListener('click', function () {
      if (!self.secUserId) { return; }
      var total = self.awemeCount === null ? '全部' : self.awemeCount;
      if (!window.confirm('确定下载该主播的' + total + '个作品？')) { return; }
      self.startDownload({ all: true, sec_user_id: self.secUserId });
    });
  };

  OwnerPosts.prototype.setStatus = function (text) {
    this.status.textContent = text;
  };

  // ---------------------------------------------------------------- reading

  OwnerPosts.prototype.read = function () {
    var self = this;
    var raw = this.urlInput.value || '';
    var url = extractUrl(raw);
    if (!url) {
      this.setStatus(raw.trim()
        ? '没有从这段文字里找到链接，请确认复制的是分享内容'
        : '请先粘贴主播主页分享链接');
      return;
    }

    this.stopPolling();
    this.reset();
    this.setStatus('读取中…（跟随分享链接并请求详情与列表，通常 8-15 秒）');

    fetch('/api/owner?url=' + encodeURIComponent(url))
      .then(function (response) {
        return response.json().then(function (body) {
          return { ok: response.ok, body: body };
        });
      })
      .then(function (result) {
        if (!result.ok) {
          self.setStatus(result.body.message || '读取失败');
          return;
        }
        var data = result.body.data;
        self.secUserId = data.sec_user_id;
        self.renderOwner(data.owner, data.owner_message, data.credential);
        self.appendPosts(data.posts);
        self.nextCursor = data.next_cursor;
        self.hasMore = data.has_more;
        self.refreshPager();
        self.toolbar.hidden = false;
        self.table.hidden = false;
        self.setStatus('已读取 ' + self.loaded + ' 个作品');
      })
      .catch(function (error) {
        self.setStatus('读取失败：' + error.message);
      });
  };

  OwnerPosts.prototype.loadMore = function () {
    var self = this;
    if (!this.secUserId || !this.hasMore) { return; }
    this.setStatus('加载更多…');

    fetch('/api/owner/posts?sec_user_id=' + encodeURIComponent(this.secUserId) +
          '&cursor=' + encodeURIComponent(this.nextCursor))
      .then(function (response) {
        return response.json().then(function (body) {
          return { ok: response.ok, body: body };
        });
      })
      .then(function (result) {
        if (!result.ok) {
          self.setStatus(result.body.message || '加载失败');
          return;
        }
        var data = result.body.data;
        self.appendPosts(data.posts);
        self.nextCursor = data.next_cursor;
        self.hasMore = data.has_more;
        self.refreshPager();
        self.setStatus('已加载 ' + self.loaded + ' 个作品');
      })
      .catch(function (error) {
        self.setStatus('加载失败：' + error.message);
      });
  };

  OwnerPosts.prototype.reset = function () {
    this.rows.innerHTML = '';
    this.loaded = 0;
    this.nextCursor = 0;
    this.hasMore = false;
    this.awemeCount = null;
    this.selectAll.checked = false;
    this.card.hidden = true;
    this.toolbar.hidden = true;
    this.table.hidden = true;
    this.pager.hidden = true;
    this.jobStatus.textContent = '';
    this.refreshSelection();
  };

  // ---------------------------------------------------------------- rendering

  function formatCount(value) {
    if (typeof value !== 'number') { return '—'; }
    if (value >= 10000) { return (value / 10000).toFixed(1) + '万'; }
    return String(value);
  }

  function formatTime(seconds) {
    if (typeof seconds !== 'number' || seconds <= 0) { return '—'; }
    var date = new Date(seconds * 1000);
    return date.getFullYear() + '-' +
      String(date.getMonth() + 1).padStart(2, '0') + '-' +
      String(date.getDate()).padStart(2, '0');
  }

  function formatDuration(milliseconds) {
    if (typeof milliseconds !== 'number' || milliseconds <= 0) { return ''; }
    var total = Math.round(milliseconds / 1000);
    return String(Math.floor(total / 60)) + ':' +
      String(total % 60).padStart(2, '0');
  }

  OwnerPosts.prototype.renderOwner = function (owner, message, credential) {
    this.card.hidden = false;
    var messageBox = this.root.querySelector('.op-owner-message');
    var credentialBox = this.root.querySelector('.op-credential');

    if (owner) {
      this.awemeCount = owner.aweme_count;
      this.root.querySelector('.op-avatar').src = owner.avatar_url || '';
      this.root.querySelector('.op-nickname').textContent = owner.nickname || '—';
      this.root.querySelector('.op-unique-id').textContent =
        owner.unique_id ? '@' + owner.unique_id : '';
      this.root.querySelector('.op-signature').textContent = owner.signature || '';
      this.root.querySelector('.op-follower').textContent =
        formatCount(owner.follower_count);
      this.root.querySelector('.op-following').textContent =
        formatCount(owner.following_count);
      this.root.querySelector('.op-aweme-count').textContent =
        formatCount(owner.aweme_count);
      this.root.querySelector('.op-favorited').textContent =
        formatCount(owner.total_favorited);
      messageBox.hidden = true;
    } else {
      messageBox.hidden = false;
      messageBox.textContent = message || '主播详情不可用';
    }

    // A cookie nearing its end is worth saying out loud: once it lapses the post
    // list comes back empty, which reads like the owner has no posts.
    var days = credential && credential.expires_in_days;
    if (typeof days === 'number') {
      credentialBox.hidden = false;
      if (days < 0) {
        credentialBox.textContent = '⚠ 登录凭据已过期，请更新 cookie';
        credentialBox.classList.add('op-credential-warn');
      } else {
        credentialBox.textContent = '登录凭据 ' + days + ' 天后过期';
        credentialBox.classList.toggle('op-credential-warn', days < 7);
      }
    } else {
      credentialBox.hidden = true;
    }
  };

  OwnerPosts.prototype.appendPosts = function (posts) {
    var self = this;
    (posts || []).forEach(function (post) {
      self.rows.appendChild(self.buildRow(post));
      self.loaded += 1;
    });
    this.refreshSelection();
  };

  OwnerPosts.prototype.buildRow = function (post) {
    var row = document.createElement('tr');
    row.dataset.awemeId = post.aweme_id;

    var selectCell = document.createElement('td');
    var box = document.createElement('input');
    box.type = 'checkbox';
    box.className = 'op-row-select';
    box.value = post.aweme_id;
    var self = this;
    box.addEventListener('change', function () { self.refreshSelection(); });
    selectCell.appendChild(box);
    row.appendChild(selectCell);

    var coverCell = document.createElement('td');
    if (post.cover_url) {
      var cover = document.createElement('img');
      cover.className = 'op-cover';
      cover.loading = 'lazy';
      cover.alt = '';
      cover.src = post.cover_url;
      // Hotlink protection may refuse these; a missing thumbnail must not look
      // like a broken page and does not affect downloading.
      cover.addEventListener('error', function () {
        cover.remove();
        coverCell.textContent = '—';
      });
      coverCell.appendChild(cover);
    } else {
      coverCell.textContent = '—';
    }
    row.appendChild(coverCell);

    var descCell = document.createElement('td');
    descCell.className = 'op-desc';
    descCell.textContent = post.desc || '（无文案）';
    if (post.aweme_type === 'image') {
      var tag = document.createElement('span');
      tag.className = 'op-tag';
      tag.textContent = '图集';
      descCell.appendChild(tag);
    }
    row.appendChild(descCell);

    var timeCell = document.createElement('td');
    timeCell.textContent = formatTime(post.create_time);
    var duration = formatDuration(post.duration);
    if (duration) {
      var small = document.createElement('small');
      small.textContent = ' ' + duration;
      timeCell.appendChild(small);
    }
    row.appendChild(timeCell);

    var statsCell = document.createElement('td');
    statsCell.textContent = '♥ ' + formatCount(post.digg_count) +
      ' 💬 ' + formatCount(post.comment_count);
    row.appendChild(statsCell);

    var stateCell = document.createElement('td');
    stateCell.className = 'op-state';
    this.paintState(stateCell, post);
    row.appendChild(stateCell);

    return row;
  };

  OwnerPosts.prototype.paintState = function (cell, post) {
    if (post.downloaded) {
      var saved = post.saved_count;
      var planned = post.media_count;
      if (typeof saved === 'number' && typeof planned === 'number' &&
          saved < planned) {
        cell.textContent = '部分 ' + saved + '/' + planned;
        cell.className = 'op-state op-state-partial';
        return;
      }
      cell.textContent = '✓ 已下载';
      cell.className = 'op-state op-state-done';
      return;
    }
    cell.textContent = '';
    cell.className = 'op-state';
  };

  OwnerPosts.prototype.refreshPager = function () {
    this.pager.hidden = !this.hasMore && this.loaded === 0;
    this.root.querySelector('.op-load-more').disabled = !this.hasMore;
    var total = this.awemeCount === null ? '?' : this.awemeCount;
    this.pageInfo.textContent = '已加载 ' + this.loaded + ' / ' + total;
  };

  // ---------------------------------------------------------------- selection

  OwnerPosts.prototype.selectedIds = function () {
    return Array.prototype.map.call(
      this.rows.querySelectorAll('.op-row-select:checked'),
      function (box) { return box.value; }
    );
  };

  OwnerPosts.prototype.refreshSelection = function () {
    var count = this.selectedIds().length;
    this.selectionInfo.textContent = '已选 ' + count + ' 个';
    this.downloadSelected.disabled = count === 0;
  };

  // ---------------------------------------------------------------- download

  OwnerPosts.prototype.startDownload = function (payload) {
    var self = this;
    var body = payload;
    body.share_url = extractUrl(this.urlInput.value);

    this.stopPolling();
    this.jobStatus.textContent = '提交中…';

    fetch('/api/owner/download', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
      .then(function (response) {
        return response.json().then(function (parsed) {
          return { ok: response.ok, body: parsed };
        });
      })
      .then(function (result) {
        if (!result.ok) {
          self.jobStatus.textContent = result.body.message || '提交失败';
          return;
        }
        self.jobId = result.body.data.job_id;
        self.poll();
      })
      .catch(function (error) {
        self.jobStatus.textContent = '提交失败：' + error.message;
      });
  };

  OwnerPosts.prototype.poll = function () {
    var self = this;
    if (!this.jobId) { return; }

    fetch('/api/owner/download/' + encodeURIComponent(this.jobId))
      .then(function (response) {
        return response.json().then(function (body) {
          return { ok: response.ok, body: body };
        });
      })
      .then(function (result) {
        if (!result.ok) {
          self.jobStatus.textContent = result.body.message || '进度不可用';
          self.stopPolling();
          return;
        }
        var data = result.body.data;
        self.applyProgress(data);
        if (data.state === 'running') {
          self.pollTimer = window.setTimeout(function () { self.poll(); },
                                             POLL_INTERVAL_MS);
          return;
        }
        self.stopPolling();
      })
      .catch(function (error) {
        self.jobStatus.textContent = '进度不可用：' + error.message;
        self.stopPolling();
      });
  };

  OwnerPosts.prototype.applyProgress = function (data) {
    var suffix = data.state === 'error' ? '（' + (data.message || '出错') + '）' : '';
    this.jobStatus.textContent =
      '下载 ' + data.finished + ' / ' + data.total + suffix;

    var self = this;
    (data.items || []).forEach(function (item) {
      var row = self.rows.querySelector(
        'tr[data-aweme-id="' + item.key + '"]'
      );
      if (!row) { return; }
      var cell = row.querySelector('.op-state');
      if (item.state === 'done') {
        self.paintState(cell, {
          downloaded: true,
          saved_count: item.saved,
          media_count: item.planned,
        });
      } else if (item.state === 'skipped') {
        cell.textContent = '✓ 已下载';
        cell.className = 'op-state op-state-done';
      } else if (item.state === 'error') {
        cell.textContent = '失败';
        cell.className = 'op-state op-state-error';
        cell.title = item.message || '';
      } else if (item.state === 'running') {
        cell.textContent = '下载中…';
        cell.className = 'op-state';
      }
    });
  };

  OwnerPosts.prototype.stopPolling = function () {
    if (this.pollTimer !== null) {
      window.clearTimeout(this.pollTimer);
      this.pollTimer = null;
    }
  };

  if (typeof document !== 'undefined') {
    document.addEventListener('DOMContentLoaded', function () {
      Array.prototype.forEach.call(
        document.querySelectorAll('.owner-posts'),
        function (root) { new OwnerPosts(root); }
      );
    });
  }
})();
