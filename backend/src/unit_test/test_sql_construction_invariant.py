import ast
import re
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATABASE_ROOT = PROJECT_ROOT / "backend/src/database"

SQL_KEYWORDS = re.compile(
  r"\b(select|insert\s+into|update|delete\s+from|create\s+table|drop\s+table)\b",
  re.IGNORECASE,
)

##
## 表名与列名无法用占位符传递，只能拼接；数据值必须走 %s 绑定。
## 这个测试锁住的正是这条界线：拼进 SQL 的实参必须能追溯到
##   - 硬编码的表名常量，或
##   - 标识符转义助手，或
##   - 纯占位符串（", ".join(["%s"] * n)）
## 其余一律视为把数据拼进了语句。
##
IDENTIFIER_CONSTANT = re.compile(r"^_{0,2}[A-Z][A-Z0-9_]*(TABLE_NAME|TABLE)$")
IDENTIFIER_HELPERS = ("_quote_identifier", "quote_identifier")
PLACEHOLDER_LITERAL = re.compile(r"""["']%s["']""")


def describe(node) -> str:
  try:
    return ast.unparse(node)
  except Exception:
    return type(node).__name__


def diagnostic_node_ids(tree) -> set:
  """收集日志与异常消息内部的全部节点。

  这类字符串常含 update / select 等词，但它们是给人看的文案，不会被执行。
  排除后，扫描才只针对真正送进 cursor.execute 的语句。
  """
  excluded = set()
  for node in ast.walk(tree):
    is_diagnostic = isinstance(node, ast.Raise)
    if isinstance(node, ast.Call):
      text = describe(node.func)
      if "get_logger" in text or text.endswith(
        (".error", ".warning", ".info", ".debug")
      ):
        is_diagnostic = True
    if is_diagnostic:
      for inner in ast.walk(node):
        excluded.add(id(inner))
  return excluded


##
## 分隔符字面量：只含空白、逗号、括号或 AND/OR，不携带数据。
##
SEPARATOR_LITERAL = re.compile(r"^[\s,()]*(?:(?:AND|OR)[\s,()]*)?$", re.IGNORECASE)


def _is_placeholder_expression(node) -> bool:
  """表达式是否只产出 %s 占位符与分隔符。"""
  constants = [
    inner.value
    for inner in ast.walk(node)
    if isinstance(inner, ast.Constant) and isinstance(inner.value, str)
  ]
  if not any(value == "%s" for value in constants):
    return False
  return all(
    value == "%s" or SEPARATOR_LITERAL.match(value) is not None for value in constants
  )


def _is_identifier_expression(node, derived: set) -> bool:
  """表达式是否只由标识符（或占位符）构成。

  先看整体：出现转义助手即认定安全。否则检查表达式里的每一个变量叶子，
  全部可追溯到标识符时才算安全 —— 这样 ``', '.join(quoted_columns)``
  这类中间形态无需逐个登记。
  """
  text = describe(node)
  if any(helper in text for helper in IDENTIFIER_HELPERS):
    return True

  if isinstance(node, ast.Attribute):
    return IDENTIFIER_CONSTANT.match(node.attr.lstrip("_")) is not None

  ##
  ## 纯占位符构造，如 ', '.join(['%s'] * len(rows))：其中的变量只决定个数，
  ## 不会有任何数据进入语句，因此先于变量检查判定。
  ##
  if _is_placeholder_expression(node):
    return True

  names = [inner for inner in ast.walk(node) if isinstance(inner, ast.Name)]
  if not names:
    return bool(PLACEHOLDER_LITERAL.search(text))

  for name in names:
    bare = name.id.lstrip("_")
    if IDENTIFIER_CONSTANT.match(bare) or IDENTIFIER_CONSTANT.match(name.id):
      continue
    if name.id in derived:
      continue
    return False
  return True


def identifier_derived_names(scope) -> set:
  """在一个作用域内，找出所有由标识符派生的变量名。

  逐轮传播直到不再增长：``header_sql = ', '.join([_quote_identifier(k) ...])``
  这类中间变量因此也被认作标识符，无需逐个写进白名单。
  """
  assignments = []
  for node in ast.walk(scope):
    if isinstance(node, ast.Assign):
      for target in node.targets:
        if isinstance(target, ast.Name):
          assignments.append((target.id, node.value))
    elif isinstance(node, (ast.AugAssign, ast.AnnAssign)):
      if isinstance(node.target, ast.Name) and node.value is not None:
        assignments.append((node.target.id, node.value))
    elif isinstance(node, ast.Call):
      ##
      ## where_conditions.append("{} = %s".format(quote(key))) 这类累积构建
      ##
      function = node.func
      if (
        isinstance(function, ast.Attribute)
        and function.attr == "append"
        and isinstance(function.value, ast.Name)
        and len(node.args) == 1
      ):
        assignments.append((function.value.id, node.args[0]))

  derived = set()
  for _ in range(4):
    grew = False
    for name, value in assignments:
      if name in derived:
        continue
      if _is_identifier_expression(value, derived):
        derived.add(name)
        grew = True
    if not grew:
      break
  return derived


def scan(path: Path):
  """返回该文件中把非标识符拼进 SQL 的位置。

  按作用域递归下降，每个节点只检查一次；进入函数时把该函数内推导出的
  标识符变量并入当前集合，离开即失效，避免不同函数间同名变量互相污染。
  """
  tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
  excluded = diagnostic_node_ids(tree)
  offenders = []

  def check(node, derived):
    if id(node) in excluded:
      return

    if isinstance(node, ast.Call):
      function = node.func
      if isinstance(function, ast.Attribute) and function.attr == "format":
        literal = function.value
        if (
          isinstance(literal, ast.Constant)
          and isinstance(literal.value, str)
          and SQL_KEYWORDS.search(literal.value)
        ):
          for argument in node.args:
            if not _is_identifier_expression(argument, derived):
              offenders.append(
                "{}:{} -> .format({})".format(
                  path.relative_to(PROJECT_ROOT), node.lineno, describe(argument)
                )
              )

    elif isinstance(node, ast.JoinedStr):
      literal_text = "".join(
        part.value
        for part in node.values
        if isinstance(part, ast.Constant) and isinstance(part.value, str)
      )
      if SQL_KEYWORDS.search(literal_text) is not None:
        for part in node.values:
          if isinstance(part, ast.FormattedValue) and not _is_identifier_expression(
            part.value, derived
          ):
            offenders.append(
              "{}:{} -> f-string 插入 {}".format(
                path.relative_to(PROJECT_ROOT), node.lineno, describe(part.value)
              )
            )

  def descend(node, derived):
    check(node, derived)
    for child in ast.iter_child_nodes(node):
      if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
        descend(child, derived | identifier_derived_names(child))
      else:
        descend(child, derived)

  descend(tree, identifier_derived_names(tree))
  return offenders


class SqlConstructionInvariantTest(unittest.TestCase):
  def test_only_identifiers_are_interpolated_into_sql(self):
    offenders = []
    for path in sorted(DATABASE_ROOT.rglob("*.py")):
      offenders.extend(scan(path))

    self.assertEqual(
      sorted(set(offenders)),
      [],
      "SQL 只允许拼接标识符，数据值必须用 %s 绑定:\n  "
      + "\n  ".join(sorted(set(offenders))),
    )

  def test_the_scanner_still_catches_a_data_value(self):
    ##
    ## 反向验证：扫描器本身必须能抓到真正的拼接，否则上一条断言毫无意义。
    ##
    sample = PROJECT_ROOT / "backend/src/unit_test/.sql_invariant_probe.py"
    sample.write_text(
      'def f(nickname):\n'
      '  sql = "UPDATE share_url SET nickname = \\"{}\\"".format(nickname)\n'
      '  return sql\n',
      encoding="utf-8",
    )
    try:
      offenders = scan(sample)
    finally:
      sample.unlink()

    self.assertEqual(1, len(offenders), offenders)
    self.assertIn("nickname", offenders[0])


if __name__ == "__main__":
  unittest.main()
