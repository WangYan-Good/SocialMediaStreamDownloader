// 下载历史列表：筛选浏览 + 手动探测直播状态
//
// 同一份逻辑服务两种形态（History 完整版 / Download 精简版），靠容器上的
// data-variant 区分。所有主播昵称、标题都用 textContent 写入，不拼 HTML，
// 因为这些内容来自平台，不可信。

(function () {
  var FILTER_DEBOUNCE_MS = 300;
  var POLL_INTERVAL_MS = 2000;

  var STATE_LABELS = {
    pending: '⏳ 排队中',
    running: '⏳ 检查中…',
    living: '🔴 正在直播',
    offline: '⚫ 未开播',
    error: '⚠️ 查询失败'
  };

  function relativeTime(isoText) {
    if (!isoText) { return '从未见到'; }
    var then = new Date(isoText).getTime();
    if (isNaN(then)) { return '从未见到'; }
    var seconds = Math.max(0, Math.floor((Date.now() - then) / 1000));
    if (seconds < 60) { return seconds + ' 秒前'; }
    if (seconds < 3600) { return Math.floor(seconds / 60) + ' 分钟前'; }
    if (seconds < 86400) { return Math.floor(seconds / 3600) + ' 小时前'; }
    return Math.floor(seconds / 86400) + ' 天前';
  }

  function lastSeenText(item) {
    if (!item.last_checked_at) { return '从未记录'; }
    if (item.last_live_status === 2) { return relativeTime(item.last_checked_at); }
    if (item.last_live_status === 4) { return relativeTime(item.last_checked_at) + '（已结束）'; }
    return relativeTime(item.last_checked_at) + '（状态未知）';
  }

  function cell(text) {
    var td = document.createElement('td');
    td.textContent = text === null || text === undefined ? '' : String(text);
    return td;
  }

  function OwnerHistory(root) {
    this.root = root;
    this.variant = root.dataset.variant || 'full';
    this.page = 1;
    this.pageSize = 10;
    this.total = 0;
    this.items = [];
    this.pollTimer = null;
    this.batchId = null;
    this.debounceTimer = null;

    this.rows = root.querySelector('.oh-rows');
    this.status = root.querySelector('.oh-status');
    this.empty = root.querySelector('.oh-empty');
    this.pageInfo = root.querySelector('.oh-page-info');
    this.selectAll = root.querySelector('.oh-select-all');

    this.bind();
    this.load();
  }

  OwnerHistory.prototype.bind = function () {
    var self = this;

    Array.prototype.forEach.call(
      this.root.querySelectorAll('.oh-filter'),
      function (control) {
        var eventName = control.tagName === 'SELECT' || control.type === 'checkbox'
          ? 'change'
          : 'input';
        control.addEventListener(eventName, function () {
          // 筛选条件变更回到第一页，并做防抖，避免连续输入触发多次查询
          clearTimeout(self.debounceTimer);
          self.debounceTimer = setTimeout(function () {
            self.page = 1;
            self.load();
          }, FILTER_DEBOUNCE_MS);
        });
      }
    );

    this.root.querySelector('.oh-prev').addEventListener('click', function () {
      if (self.page > 1) { self.page -= 1; self.load(); }
    });
    this.root.querySelector('.oh-next').addEventListener('click', function () {
      if (self.page * self.pageSize < self.total) { self.page += 1; self.load(); }
    });
    this.root.querySelector('.oh-probe-button').addEventListener('click', function () {
      self.probe();
    });
    if (this.selectAll) {
      this.selectAll.addEventListener('change', function () {
        Array.prototype.forEach.call(
          self.rows.querySelectorAll('.oh-row-select'),
          function (box) { box.checked = self.selectAll.checked; }
        );
      });
    }
  };

  OwnerHistory.prototype.filterParams = function () {
    var params = new URLSearchParams();
    Array.prototype.forEach.call(
      this.root.querySelectorAll('.oh-filter'),
      function (control) {
        var key = control.dataset.filter;
        var value = control.type === 'checkbox'
          ? (control.checked ? 'true' : '')
          : control.value.trim();
        if (value) { params.set(key, value); }
      }
    );
    params.set('page', String(this.page));
    return params;
  };

  OwnerHistory.prototype.setStatus = function (text) {
    this.status.textContent = text;
  };

  OwnerHistory.prototype.load = function () {
    var self = this;
    this.stopPolling();
    this.setStatus('加载中…');

    fetch('/api/history/owners?' + this.filterParams().toString())
      .then(function (response) {
        return response.json().then(function (body) {
          return { ok: response.ok, body: body };
        });
      })
      .then(function (result) {
        if (!result.ok) {
          self.rows.replaceChildren();
          self.setStatus(result.body.message || '加载失败');
          return;
        }
        var data = result.body.data;
        self.total = data.total;
        self.pageSize = data.page_size;
        self.items = data.items;
        self.render();
        self.setStatus('共 ' + data.total + ' 条');
      })
      .catch(function (error) {
        self.setStatus('加载失败：' + error.message);
      });
  };

  OwnerHistory.prototype.render = function () {
    var self = this;
    this.rows.replaceChildren();
    this.empty.hidden = this.items.length > 0;

    this.items.forEach(function (item) {
      var tr = document.createElement('tr');
      tr.dataset.ownerUserId = item.owner_user_id;

      var selectCell = document.createElement('td');
      var box = document.createElement('input');
      box.type = 'checkbox';
      box.className = 'oh-row-select';
      selectCell.appendChild(box);
      tr.appendChild(selectCell);

      var nameCell = document.createElement('td');
      nameCell.textContent = item.nickname || '(无昵称)';
      if (self.variant === 'full') {
        // 完整版点昵称展开该主播的历史场次
        nameCell.className = 'oh-expandable';
        nameCell.addEventListener('click', function () {
          self.toggleSessions(tr, item.owner_user_id);
        });
      }
      tr.appendChild(nameCell);

      if (self.variant === 'full') {
        tr.appendChild(cell(item.score === null ? '—' : item.score));
        tr.appendChild(cell(item.actived_count));
        tr.appendChild(cell(lastSeenText(item)));
      }

      var stateCell = document.createElement('td');
      stateCell.className = 'oh-state';
      stateCell.textContent = '—';
      tr.appendChild(stateCell);

      var actionCell = document.createElement('td');
      actionCell.className = 'oh-action';
      tr.appendChild(actionCell);

      self.rows.appendChild(tr);
    });

    if (this.selectAll) { this.selectAll.checked = false; }
    var pages = Math.max(1, Math.ceil(this.total / this.pageSize));
    this.pageInfo.textContent = '第 ' + this.page + ' / ' + pages + ' 页';
  };

  OwnerHistory.prototype.selectedOwnerIds = function () {
    var checked = Array.prototype.filter.call(
      this.rows.querySelectorAll('.oh-row-select'),
      function (box) { return box.checked; }
    );
    var source = checked.length > 0
      ? checked.map(function (box) { return box.closest('tr'); })
      : Array.prototype.slice.call(this.rows.querySelectorAll('tr[data-owner-user-id]'));
    return source.map(function (tr) { return tr.dataset.ownerUserId; });
  };

  OwnerHistory.prototype.probe = function () {
    var self = this;
    var ownerIds = this.selectedOwnerIds();
    if (ownerIds.length === 0) {
      this.setStatus('没有可检查的记录');
      return;
    }

    this.stopPolling();
    this.setStatus('正在检查 ' + ownerIds.length + ' 个主播（每个约 5-12 秒）…');

    fetch('/api/live/probe', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ owner_user_ids: ownerIds })
    })
      .then(function (response) {
        return response.json().then(function (body) {
          return { ok: response.ok, body: body };
        });
      })
      .then(function (result) {
        if (!result.ok) {
          self.setStatus(result.body.message || '提交检查失败');
          return;
        }
        self.batchId = result.body.data.batch_id;
        self.applyProbe(result.body.data);
        if (result.body.data.done) {
          // 整批命中缓存时首个响应就已经是终态，此时不会有轮询来收尾
          self.setStatus('检查完成');
        } else {
          self.startPolling();
        }
      })
      .catch(function (error) {
        self.setStatus('提交检查失败：' + error.message);
      });
  };

  OwnerHistory.prototype.startPolling = function () {
    var self = this;
    this.pollTimer = setInterval(function () {
      fetch('/api/live/probe/' + self.batchId)
        .then(function (response) { return response.json(); })
        .then(function (body) {
          if (!body.data) { self.stopPolling(); return; }
          self.applyProbe(body.data);
          if (body.data.done) {
            self.stopPolling();
            self.setStatus('检查完成');
          }
        })
        .catch(function () { self.stopPolling(); });
    }, POLL_INTERVAL_MS);
  };

  OwnerHistory.prototype.stopPolling = function () {
    if (this.pollTimer !== null) {
      clearInterval(this.pollTimer);
      this.pollTimer = null;
    }
  };

  OwnerHistory.prototype.applyProbe = function (data) {
    var self = this;
    data.items.forEach(function (item) {
      var tr = self.rows.querySelector(
        'tr[data-owner-user-id="' + CSS.escape(item.owner_user_id) + '"]'
      );
      if (!tr) { return; }

      var stateCell = tr.querySelector('.oh-state');
      stateCell.textContent = STATE_LABELS[item.state] || item.state;
      stateCell.className = 'oh-state oh-state-' + item.state;
      if (item.state === 'error' && item.message) {
        stateCell.title = item.message;
      }
      if (item.cached) {
        stateCell.textContent += '（缓存）';
      }

      var actionCell = tr.querySelector('.oh-action');
      actionCell.replaceChildren();
      if (item.state === 'living' && item.live_share_url) {
        var button = document.createElement('button');
        button.type = 'button';
        button.textContent = '立即下载';
        button.addEventListener('click', function () {
          self.download(item.live_share_url, button);
        });
        actionCell.appendChild(button);
      }
    });
  };

  OwnerHistory.prototype.download = function (shareUrl, button) {
    var self = this;
    button.disabled = true;
    button.textContent = '已提交';
    // 复用既有的下载入口，请求体形状与 submit.js 保持一致
    fetch('/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ urls: [shareUrl], score: 0, favorite: false })
    })
      .then(function (response) {
        if (!response.ok) { throw new Error('提交失败'); }
        self.setStatus('已开始下载');
      })
      .catch(function (error) {
        button.disabled = false;
        button.textContent = '立即下载';
        self.setStatus('下载提交失败：' + error.message);
      });
  };

  OwnerHistory.prototype.toggleSessions = function (tr, ownerUserId) {
    var existing = tr.nextElementSibling;
    if (existing && existing.classList.contains('oh-sessions')) {
      existing.remove();
      return;
    }

    var self = this;
    var row = document.createElement('tr');
    row.className = 'oh-sessions';
    var container = document.createElement('td');
    container.colSpan = tr.children.length;
    container.textContent = '加载场次…';
    row.appendChild(container);
    tr.insertAdjacentElement('afterend', row);

    fetch('/api/history/owners/' + encodeURIComponent(ownerUserId) + '/sessions?limit=20')
      .then(function (response) { return response.json(); })
      .then(function (body) {
        container.replaceChildren();
        var sessions = (body.data && body.data.items) || [];
        if (sessions.length === 0) {
          container.textContent = '没有场次记录';
          return;
        }
        var list = document.createElement('ul');
        sessions.forEach(function (session) {
          var entry = document.createElement('li');
          entry.textContent = relativeTime(session.observed_at)
            + ' · ' + (session.room_status === 2 ? '直播中' : '已结束')
            + (session.title ? ' · ' + session.title : '');
          list.appendChild(entry);
        });
        container.appendChild(list);
      })
      .catch(function (error) {
        container.textContent = '场次加载失败：' + error.message;
      });
    void self;
  };

  document.addEventListener('DOMContentLoaded', function () {
    Array.prototype.forEach.call(
      document.querySelectorAll('.owner-history'),
      function (root) { new OwnerHistory(root); }
    );
  });
})();
