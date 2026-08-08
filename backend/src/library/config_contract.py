from collections.abc import Mapping


class ConfigContractError(ValueError):
  """Safe validation error containing only missing reference paths."""

  def __init__(self, issues: tuple[str, ...]):
    self.issues = tuple(issues)
    super().__init__(
      "configuration contract validation failed: " + ", ".join(self.issues)
    )


def find_config_contract_issues(
  reference: object,
  actual: object,
  path: str = "$",
) -> tuple[str, ...]:
  """Return required reference paths that are absent from ``actual``.

  Only reference mappings define the required structure.  Leaves need only
  exist; their values and types are intentionally not compared.
  """
  if not isinstance(reference, Mapping):
    raise ValueError("reference configuration root must be a mapping")
  if not isinstance(actual, Mapping):
    return ("$",)

  issues: list[str] = []
  for key, reference_value in reference.items():
    child_path = f"{path}.{key}"
    if key not in actual:
      issues.append(child_path)
      continue

    if isinstance(reference_value, Mapping):
      actual_value = actual[key]
      if not isinstance(actual_value, Mapping):
        issues.append(child_path)
      else:
        issues.extend(
          find_config_contract_issues(reference_value, actual_value, child_path)
        )

  return tuple(issues)


def validate_config_contract(reference: object, actual: object) -> None:
  """Raise a safe error if actual configuration misses reference structure."""
  issues = find_config_contract_issues(reference, actual)
  if issues:
    raise ConfigContractError(issues)
