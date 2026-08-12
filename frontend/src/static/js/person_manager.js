/*
 * Person management.
 *
 * Every relationship here is entered by hand: nicknames cannot supply them, since
 * of 1815 accounts there are 1785 distinct nicknames, so the same person's
 * accounts almost never share a name.
 */
(function () {
  'use strict';

  var ROLE_LABELS = { main: '主号', alt: '小号', matrix: '矩阵号' };

  function request(method, url, body) {
    var options = { method: method, headers: {} };
    if (body !== undefined) {
      options.headers['Content-Type'] = 'application/json';
      options.body = JSON.stringify(body);
    }
    return fetch(url, options).then(function (response) {
      return response.json().then(function (parsed) {
        if (!response.ok) {
          throw new Error((parsed && parsed.message) || '请求失败');
        }
        return parsed.data;
      });
    });
  }

  function element(tag, className, text) {
    var node = document.createElement(tag);
    if (className) { node.className = className; }
    if (text !== undefined && text !== null) { node.textContent = text; }
    return node;
  }

  function PersonManager(root) {
    this.root = root;
    this.people = root.querySelector('.pm-people');
    this.status = root.querySelector('.pm-status');
    this.newName = root.querySelector('.pm-new-name');
    this.newDirectory = root.querySelector('.pm-new-directory');
    this.attachPanel = root.querySelector('.pm-attach');
    this.attachPersonName = root.querySelector('.pm-attach-person');
    this.searchInput = root.querySelector('.pm-search');
    this.roleSelect = root.querySelector('.pm-role');
    this.results = root.querySelector('.pm-results');
    this.attachingTo = null;

    root.querySelector('.pm-create-button')
        .addEventListener('click', this.createPerson.bind(this));
    root.querySelector('.pm-search-button')
        .addEventListener('click', this.searchAccounts.bind(this));
    root.querySelector('.pm-attach-close')
        .addEventListener('click', this.closeAttach.bind(this));
    this.searchInput.addEventListener('keydown', function (event) {
      if (event.key === 'Enter') { this.searchAccounts(); }
    }.bind(this));

    this.refresh();
  }

  PersonManager.prototype.say = function (message) {
    this.status.textContent = message;
  };

  PersonManager.prototype.refresh = function () {
    var self = this;
    return request('GET', '/api/person')
      .then(function (data) { self.render(data.persons || []); })
      .catch(function (error) { self.say('读取失败：' + error.message); });
  };

  PersonManager.prototype.render = function (persons) {
    this.people.innerHTML = '';
    if (!persons.length) {
      this.say('还没有建立任何人物。建一个，再把他的账号挂上去。');
      return;
    }
    this.say('共 ' + persons.length + ' 个人物');
    persons.forEach(this.renderPerson.bind(this));
  };

  PersonManager.prototype.renderPerson = function (person) {
    var self = this;
    var card = element('div', 'pm-person');

    var head = element('div', 'pm-person-head');
    head.appendChild(element('span', 'pm-person-name', person.display_name));
    head.appendChild(element(
      'span',
      'pm-person-directory',
      person.directory_name ? '目录：' + person.directory_name : '未设归并目录'
    ));
    head.appendChild(element(
      'span',
      'pm-person-count',
      '账号 ' + (person.account_count || 0)
    ));
    card.appendChild(head);

    var actions = element('div', 'pm-person-actions');

    var attach = element('button', 'pm-action', '挂载账号');
    attach.addEventListener('click', function () { self.openAttach(person); });
    actions.appendChild(attach);

    var rename = element('button', 'pm-action', '改目录');
    rename.addEventListener('click', function () {
      var next = window.prompt('归并目录名', person.directory_name || '');
      if (next === null) { return; }
      request('PATCH', '/api/person/' + person.person_id,
              { directory_name: next.trim() })
        .then(function () { return self.refresh(); })
        .catch(function (error) { self.say('修改失败：' + error.message); });
    });
    actions.appendChild(rename);

    var remove = element('button', 'pm-action pm-danger', '删除');
    remove.addEventListener('click', function () {
      if (!window.confirm('删除「' + person.display_name +
                          '」？其账号归属与合作关系会一并消失，已下载的文件不受影响。')) {
        return;
      }
      request('DELETE', '/api/person/' + person.person_id)
        .then(function () { return self.refresh(); })
        .catch(function (error) { self.say('删除失败：' + error.message); });
    });
    actions.appendChild(remove);

    card.appendChild(actions);
    this.people.appendChild(card);
  };

  PersonManager.prototype.createPerson = function () {
    var self = this;
    var name = (this.newName.value || '').trim();
    if (!name) {
      this.say('先填一个名字');
      return;
    }
    request('POST', '/api/person', {
      display_name: name,
      directory_name: (this.newDirectory.value || '').trim()
    })
      .then(function () {
        self.newName.value = '';
        self.newDirectory.value = '';
        return self.refresh();
      })
      .catch(function (error) { self.say('创建失败：' + error.message); });
  };

  PersonManager.prototype.openAttach = function (person) {
    this.attachingTo = person;
    this.attachPersonName.textContent = person.display_name;
    this.results.innerHTML = '';
    this.searchInput.value = '';
    this.attachPanel.hidden = false;
    this.searchInput.focus();
  };

  PersonManager.prototype.closeAttach = function () {
    this.attachingTo = null;
    this.attachPanel.hidden = true;
  };

  PersonManager.prototype.searchAccounts = function () {
    var self = this;
    var keyword = (this.searchInput.value || '').trim();
    if (!keyword) { return; }
    request('GET', '/api/person/accounts?keyword=' + encodeURIComponent(keyword))
      .then(function (data) { self.renderResults(data.accounts || []); })
      .catch(function (error) { self.say('搜索失败：' + error.message); });
  };

  PersonManager.prototype.renderResults = function (accounts) {
    var self = this;
    this.results.innerHTML = '';
    if (!accounts.length) {
      this.results.appendChild(element('p', 'pm-empty', '没有匹配的账号'));
      return;
    }
    accounts.forEach(function (account) {
      var row = element('div', 'pm-result');
      row.appendChild(element('span', 'pm-result-name', account.nickname || '(无昵称)'));
      row.appendChild(element('span', 'pm-result-id', account.owner_user_id));

      /* 已挂在别人名下时要看得见，挂载是移动而不是静默覆盖 */
      if (account.person_id) {
        row.appendChild(element(
          'span',
          'pm-result-taken',
          '已属于人物 #' + account.person_id +
            (account.role ? '（' + (ROLE_LABELS[account.role] || account.role) + '）' : '')
        ));
      }

      var attach = element('button', 'pm-action', '挂到此人');
      attach.addEventListener('click', function () {
        if (!self.attachingTo) { return; }
        request('POST', '/api/person/account', {
          owner_user_id: account.owner_user_id,
          person_id: self.attachingTo.person_id,
          role: self.roleSelect.value
        })
          .then(function () {
            self.say('已挂载 ' + (account.nickname || account.owner_user_id));
            return self.refresh();
          })
          .then(function () { self.searchAccounts(); })
          .catch(function (error) { self.say('挂载失败：' + error.message); });
      });
      row.appendChild(attach);

      if (account.person_id) {
        var detach = element('button', 'pm-action', '解除');
        detach.addEventListener('click', function () {
          request('DELETE', '/api/person/account?owner_user_id=' +
                  encodeURIComponent(account.owner_user_id))
            .then(function () {
              self.say('已解除，该账号回到自己的目录');
              return self.refresh();
            })
            .then(function () { self.searchAccounts(); })
            .catch(function (error) { self.say('解除失败：' + error.message); });
        });
        row.appendChild(detach);
      }

      self.results.appendChild(row);
    });
  };

  document.addEventListener('DOMContentLoaded', function () {
    var root = document.querySelector('.person-manager');
    if (root) { new PersonManager(root); }
  });
})();
