##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Base>>
from copy import deepcopy
from typing import Any, Mapping, Optional

## <<Third-Part>>
from backend.src.database.schema_guard import SchemaState
from backend.src.library.baselib import get_dict_attr


##
## What the system page is allowed to know.
##
## This module is the security boundary of that page. The configuration it is
## handed holds database credentials, platform cookies, tokens, proxies and
## absolute paths; what leaves here is built by naming every field that may be
## published, starting from nothing.
##
## Deliberately not the other way round. Copying the configuration and deleting
## what looks sensitive works exactly until somebody adds a field - and then it
## fails silently, in the direction of disclosure. A whitelist fails the other
## way: a new field is missing from the page until somebody decides it belongs
## there, which is a bug report rather than a leak.
##
## Nothing here reads a file, an environment variable or a network. The only
## input is a configuration mapping the server already loaded and validated.
##


##
## One public sentence per state. The guard's own ``reason`` is deliberately not
## used: it is an internal explanation that may name a host or a revision, and
## publishing it would turn the guard's wording into an api contract.
##
DATABASE_STATE_MESSAGES = {
  SchemaState.READY.value: "数据库架构已就绪",
  SchemaState.UNAVAILABLE.value: "数据库当前不可用",
  SchemaState.BLOCKED.value: "数据库架构状态阻止写入",
  SchemaState.DISABLED.value: "数据库持久化已禁用",
  ##
  ## No guard installed, or one that failed in a way nobody anticipated. Said
  ## plainly rather than guessed at in either direction.
  ##
  "unknown": "无法确认数据库状态",
}

DATABASE_STATE_UNKNOWN = "unknown"


def _value(config: Mapping[str, Any], path: str) -> Any:
  """Read one configured value, or ``None`` when it is not there.

  A partially configured server is exactly when somebody opens this page, so a
  missing section reports as unknown rather than raising.
  """
  try:
    found = get_dict_attr(config, path)
  except Exception:
    return None
  ##
  ## Copied on the way out: the snapshot must not be a live view of a mapping
  ## somebody else can still edit.
  ##
  return deepcopy(found) if isinstance(found, (dict, list)) else found


def build_safe_config_snapshot(config: Mapping[str, Any]) -> dict:
  """Return the only part of the configuration that may reach a browser.

  Every field is named. Adding a section here is a deliberate act, and anything
  not named - including whole subtrees this project has not seen yet - simply
  does not travel.
  """
  config = config or {}

  return {
    ##
    ## The bind host and port are omitted: they describe where this process
    ## listens, which is infrastructure rather than something the operator of a
    ## page needs, and one of them is often the only thing between an internal
    ## service and somebody scanning for it.
    ##
    "server": {
      "debug_mode": _value(config, "$.server.debug_mode"),
    },
    ##
    ## Whether logging happens, and how loudly. Never where it lands, and never
    ## a line of it - the log file holds urls, creator identities and upstream
    ## errors, and this project has no redaction contract for any of that.
    ##
    "logging": {
      "enabled": _value(config, "$.log.log_enable"),
      "level": _value(config, "$.log.log_level"),
      "save_enabled": _value(config, "$.log.log_save"),
    },
    ##
    ## How downloads behave. `save_path` is omitted: it is a real path on the
    ## server's filesystem.
    ##
    "download": {
      "test_mode": _value(config, "$.download.test_mode"),
      "folderize": _value(config, "$.download.folderize"),
      "listening": _value(config, "$.download.listening"),
      "user_login": _value(config, "$.download.user_login"),
    },
    "history": {
      "page_size_limit": _value(config, "$.history.page_size_limit"),
    },
    ##
    ## Platform behaviour, minus every endpoint, header, cookie and token. The
    ## `api`, `headers`, `login` and `post` subtrees are the ones that carry
    ## credentials, and none of them is named anywhere in this file.
    ##
    "douyin": {
      "aweme": {
        "concurrency": _value(config, "$.platform.douyin.aweme.concurrency"),
        "html_fallback": _value(config, "$.platform.douyin.aweme.html_fallback"),
        "skip_downloaded": _value(config, "$.platform.douyin.aweme.skip_downloaded"),
        "video_quality": _value(config, "$.platform.douyin.aweme.video_quality"),
        "media": {
          "video": _value(config, "$.platform.douyin.aweme.media.video"),
          "images": _value(config, "$.platform.douyin.aweme.media.images"),
          "music": _value(config, "$.platform.douyin.aweme.media.music"),
          "cover": _value(config, "$.platform.douyin.aweme.media.cover"),
        },
      },
      "owner": {
        "page_size": _value(config, "$.platform.douyin.owner.page_size"),
        "download_concurrency": _value(
          config, "$.platform.douyin.owner.download_concurrency"
        ),
      },
      "live_probe": {
        "max_batch_size": _value(
          config, "$.platform.douyin.live.probe.max_batch_size"
        ),
        "concurrency": _value(config, "$.platform.douyin.live.probe.concurrency"),
        "cache_ttl_seconds": _value(
          config, "$.platform.douyin.live.probe.cache_ttl_seconds"
        ),
      },
    },
  }


def describe_database(enabled: bool, snapshot: Optional[Any]) -> dict:
  """Turn a guard snapshot into the four things the page may know.

  ``reason`` and ``checked_at`` are both dropped. The first is internal wording;
  the second is a monotonic clock reading, which is not a time of day and would
  be a wrong one if shown as such. When a browser wants to know how fresh this
  is, the honest answer is when *it* received the response.
  """
  if snapshot is None:
    state = DATABASE_STATE_UNKNOWN
  else:
    state = getattr(snapshot.state, "value", str(snapshot.state))

  return {
    "enabled": bool(enabled),
    "state": state,
    ##
    ## Only a schema the guard positively reports as ready allows writes.
    ## Anything else - including a state this build does not recognise - is not
    ## write ready, because the failure of assuming otherwise is data loss.
    ##
    "write_ready": state == SchemaState.READY.value,
    "message": DATABASE_STATE_MESSAGES.get(
      state, DATABASE_STATE_MESSAGES[DATABASE_STATE_UNKNOWN]
    ),
  }
