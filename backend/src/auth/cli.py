##<<Base>>
import argparse
import getpass
import sys

##<<Third-part>>
from backend.src.auth.credentials import CredentialPolicyError
from backend.src.auth.errors import AuthUnavailable, DuplicateUsername, UnknownUsername
from backend.src.auth.roles import APP_USER_ROLES, ROLE_USER


##
## >>============================= why accounts are made here =============================>>
##
##
## There is no sign-up endpoint, on purpose.  Nothing is owned by anybody yet
## and no endpoint checks permissions, so a self-service account would be an
## account that can already see everything in the deployment.  Until ownership
## and authorization exist, an account is something whoever runs the server
## creates deliberately - which is what this command is for.
##


UNAVAILABLE_MESSAGE = "认证服务暂时不可用：数据库不可用或数据库结构尚未升级到当前版本"


def _prompt(label: str) -> str:
  ##
  ## getpass, never input: a password echoed to the terminal is a password in
  ## the scrollback, and one read from a visible prompt is one a shoulder can
  ## read.
  ##
  return getpass.getpass(label)


def create_user_command(
  username: str,
  *,
  service_factory,
  prompt=_prompt,
  out=sys.stdout,
  role=ROLE_USER,
) -> int:
  """Create one application account. Returns a process exit code."""
  try:
    service = service_factory()
  except AuthUnavailable:
    ##
    ## The reason is deliberately not printed. It carries a driver string, a
    ## host and sometimes a statement, and this command is frequently run with
    ## its output captured.
    ##
    print(UNAVAILABLE_MESSAGE, file=out)
    return 2

  try:
    password = prompt("Password: ")
    confirmation = prompt("Confirm password: ")
  except (EOFError, KeyboardInterrupt):
    ##
    ## Ctrl-C, Ctrl-D, or no terminal attached at all - a script, a pipeline, a
    ## CI step that did not expect to be asked for anything. A traceback here
    ## reads as a crash; this is just somebody changing their mind.
    ##
    print("已取消，未创建任何账户", file=out)
    return 1

  if password != confirmation:
    ##
    ## Asked twice because nobody can see what they typed. A typo discovered at
    ## the first failed login is a typo nobody can reconstruct.
    ##
    print("两次输入的密码不一致", file=out)
    return 1

  try:
    user = service.create_user(username, password, role=role)
  except CredentialPolicyError as e:
    ##
    ## The policy's own message - "密码至少需要 10 个字符" - which is about what
    ## was typed rather than about how anything is stored.
    ##
    print(str(e), file=out)
    return 1
  except DuplicateUsername:
    print("用户名已存在：{}".format(username.strip()), file=out)
    return 1
  except AuthUnavailable:
    print(UNAVAILABLE_MESSAGE, file=out)
    return 2

  ##
  ## The username and the id, and nothing else. Never the password, never the
  ## hash.
  ##
  print(
    "已创建用户 {}（user_id={}，role={}）".format(
      user.username, user.user_id, user.role
    ),
    file=out,
  )
  return 0


def set_role_command(
  username: str,
  role: str,
  *,
  service_factory,
  out=sys.stdout,
) -> int:
  """Change one account's role without touching its existing sessions."""
  try:
    service = service_factory()
    user = service.set_role(username, role)
  except UnknownUsername:
    print("用户名不存在：{}".format(username.strip()), file=out)
    return 1
  except (ValueError, TypeError) as e:
    print(str(e), file=out)
    return 1
  except AuthUnavailable:
    print(UNAVAILABLE_MESSAGE, file=out)
    return 2

  print(
    "已设置用户 {} 的角色为 {}".format(user.username, user.role),
    file=out,
  )
  return 0


def set_password_command(
  username: str,
  *,
  service_factory,
  prompt=_prompt,
  out=sys.stdout,
) -> int:
  """Rotate a password without accepting or printing it outside getpass."""
  try:
    service = service_factory()
  except AuthUnavailable:
    print(UNAVAILABLE_MESSAGE, file=out)
    return 2
  try:
    password = prompt("New password: ")
    confirmation = prompt("Confirm new password: ")
  except (EOFError, KeyboardInterrupt):
    print("已取消，密码未修改", file=out)
    return 1
  if password != confirmation:
    print("两次输入的密码不一致", file=out)
    return 1
  try:
    user = service.set_password(username, password)
  except CredentialPolicyError as error:
    print(str(error), file=out)
    return 1
  except UnknownUsername:
    print("用户名不存在：{}".format(username.strip()), file=out)
    return 1
  except AuthUnavailable:
    print(UNAVAILABLE_MESSAGE, file=out)
    return 2
  print("已更新用户 {} 的密码并撤销全部会话".format(user.username), file=out)
  return 0


def _lifecycle_command(
  username: str,
  method: str,
  success_message: str,
  *,
  service_factory,
  out=sys.stdout,
) -> int:
  try:
    service = service_factory()
    user = getattr(service, method)(username)
  except UnknownUsername:
    print("用户名不存在：{}".format(username.strip()), file=out)
    return 1
  except (ValueError, TypeError) as error:
    print(str(error), file=out)
    return 1
  except AuthUnavailable:
    print(UNAVAILABLE_MESSAGE, file=out)
    return 2
  print(success_message.format(username=user.username), file=out)
  return 0


def disable_user_command(username: str, *, service_factory, out=sys.stdout) -> int:
  return _lifecycle_command(
    username,
    "disable_user",
    "已禁用用户 {username} 并撤销全部会话",
    service_factory=service_factory,
    out=out,
  )


def enable_user_command(username: str, *, service_factory, out=sys.stdout) -> int:
  return _lifecycle_command(
    username,
    "enable_user",
    "已启用用户 {username}；需要重新登录",
    service_factory=service_factory,
    out=out,
  )


def revoke_sessions_command(
  username: str, *, service_factory, out=sys.stdout
) -> int:
  return _lifecycle_command(
    username,
    "revoke_all_sessions",
    "已撤销用户 {username} 的全部会话",
    service_factory=service_factory,
    out=out,
  )


def build_cli_service_factory(
  *,
  config_loader=None,
  guard_initializer=None,
  runtime_builder=None,
):
  """Build the CLI runtime only after installing a real schema guard."""
  if config_loader is None:
    from backend.src.library.configlib import load_config

    config_loader = load_config
  if guard_initializer is None:
    from backend.src.database.schema_guard import initialize_schema_guard

    guard_initializer = initialize_schema_guard
  if runtime_builder is None:
    from backend.src.web.auth_routes import build_auth_runtime

    runtime_builder = build_auth_runtime
  settings = config_loader()
  guard_initializer(settings)
  runtime = runtime_builder(lambda: settings)
  return runtime.service


def build_parser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser(
    prog="python -m backend.src.auth_cli",
    description="管理应用登录账户（与平台 user 表无关）",
  )
  subcommands = parser.add_subparsers(dest="command", required=True)

  ##
  ## Deliberately no --password. A password in argv is a password in shell
  ## history, in ps output for every user on the machine, and in any CI log
  ## that echoes the commands it runs.
  ##
  create = subcommands.add_parser("create-user", help="创建一个应用登录账户")
  create.add_argument("username", help="登录用户名")
  create.add_argument(
    "--role",
    choices=APP_USER_ROLES,
    default=ROLE_USER,
    help="账户角色（默认：user）",
  )

  set_role = subcommands.add_parser("set-role", help="设置应用登录账户角色")
  set_role.add_argument("username", help="登录用户名")
  set_role.add_argument("role", choices=APP_USER_ROLES, help="目标角色")

  set_password = subcommands.add_parser(
    "set-password", help="重置密码并撤销该用户全部会话"
  )
  set_password.add_argument("username", help="登录用户名")

  disable = subcommands.add_parser(
    "disable-user", help="禁用用户并撤销该用户全部会话"
  )
  disable.add_argument("username", help="登录用户名")

  enable = subcommands.add_parser("enable-user", help="启用用户")
  enable.add_argument("username", help="登录用户名")

  revoke = subcommands.add_parser(
    "revoke-sessions", help="撤销该用户全部会话"
  )
  revoke.add_argument("username", help="登录用户名")

  return parser


def main(argv=None) -> int:
  parser = build_parser()
  arguments = parser.parse_args(argv)
  service_factory = build_cli_service_factory()

  if arguments.command == "create-user":
    return create_user_command(
      arguments.username,
      service_factory=service_factory,
      role=arguments.role,
    )

  if arguments.command == "set-role":
    return set_role_command(
      arguments.username,
      arguments.role,
      service_factory=service_factory,
    )

  if arguments.command == "set-password":
    return set_password_command(
      arguments.username, service_factory=service_factory
    )

  if arguments.command == "disable-user":
    return disable_user_command(
      arguments.username, service_factory=service_factory
    )

  if arguments.command == "enable-user":
    return enable_user_command(
      arguments.username, service_factory=service_factory
    )

  if arguments.command == "revoke-sessions":
    return revoke_sessions_command(
      arguments.username, service_factory=service_factory
    )

  parser.error("unknown command")
  return 2
