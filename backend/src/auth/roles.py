"""The complete application role vocabulary and its two-level hierarchy."""


ROLE_USER = "user"
ROLE_ADMIN = "admin"

APP_USER_ROLES = (
  ROLE_USER,
  ROLE_ADMIN,
)

_ROLE_LEVEL = {
  ROLE_USER: 1,
  ROLE_ADMIN: 2,
}


class RoleValidationError(ValueError):
  """A value is not one of the roles this application understands."""


def validate_role(role: str) -> str:
  """Return a valid role unchanged and reject every other spelling/value."""
  if type(role) is not str or role not in APP_USER_ROLES:
    raise RoleValidationError(
      "role must be one of: {}".format(", ".join(APP_USER_ROLES))
    )
  return role


def role_satisfies(actual_role: str, required_role: str) -> bool:
  """Whether ``actual_role`` includes the capability of ``required_role``."""
  actual = validate_role(actual_role)
  required = validate_role(required_role)
  return _ROLE_LEVEL[actual] >= _ROLE_LEVEL[required]


__all__ = [
  "APP_USER_ROLES",
  "ROLE_ADMIN",
  "ROLE_USER",
  "RoleValidationError",
  "role_satisfies",
  "validate_role",
]
