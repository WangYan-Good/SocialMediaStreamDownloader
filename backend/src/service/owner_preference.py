from dataclasses import dataclass


PREFERENCE_PLATFORM = "douyin"
PREFERENCE_FIELDS = frozenset(("favorite", "score"))


class OwnerPreferenceValidationError(ValueError):
  """The requested preference does not satisfy the public contract."""


class OwnerNotFound(LookupError):
  """The account is not part of local History and must not gain an orphan row."""


@dataclass(frozen=True)
class OwnerPreferenceResult:
  owner_user_id: str
  favorite: bool
  score: int | None


class OwnerPreferenceService:
  """Manage one known creator account's persistent listening preference."""

  def __init__(self, repository) -> None:
    if repository is None:
      raise ValueError("repository is required")
    self._repository = repository

  def update(self, owner_user_id: str, payload) -> OwnerPreferenceResult:
    if not isinstance(owner_user_id, str) or not owner_user_id.strip():
      raise OwnerPreferenceValidationError("owner_user_id 不能为空")
    owner_user_id = owner_user_id.strip()

    if not isinstance(payload, dict):
      raise OwnerPreferenceValidationError("请求体为空或格式错误")
    unknown = set(payload) - PREFERENCE_FIELDS
    if unknown:
      raise OwnerPreferenceValidationError(
        "不支持的字段: {}".format(", ".join(sorted(unknown)))
      )

    favorite = payload.get("favorite")
    if type(favorite) is not bool:
      raise OwnerPreferenceValidationError("favorite 必须是 boolean")

    if favorite:
      if "score" not in payload:
        raise OwnerPreferenceValidationError("收藏主播时必须提供 score")
      score = payload.get("score")
      if type(score) is not int or not 0 <= score <= 100:
        raise OwnerPreferenceValidationError("score 必须是 0 到 100 的整数")
    else:
      if "score" in payload:
        raise OwnerPreferenceValidationError("取消收藏时不能提供 score")
      score = None

    if not self._repository.owner_exists(owner_user_id):
      raise OwnerNotFound("主播账号不存在或尚未进入历史记录")

    if favorite:
      self._repository.upsert_owner_preference(
        owner_user_id, score, platform=PREFERENCE_PLATFORM
      )
    else:
      self._repository.delete_owner_preference(
        owner_user_id, platform=PREFERENCE_PLATFORM
      )

    return OwnerPreferenceResult(
      owner_user_id=owner_user_id,
      favorite=favorite,
      score=score,
    )


__all__ = [
  "OwnerNotFound",
  "OwnerPreferenceResult",
  "OwnerPreferenceService",
  "OwnerPreferenceValidationError",
  "PREFERENCE_PLATFORM",
]
