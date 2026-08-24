##<<Base>>
import argparse
import getpass
import sys

##<<Third-part>>
from backend.src.auth.credentials import CredentialPolicyError
from backend.src.auth.errors import AuthUnavailable, DuplicateUsername


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


UNAVAILABLE_MESSAGE = "认证服务暂时不可用：数据库不可用或数据库结构尚未升级到 0007"


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
    user = service.create_user(username, password)
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
  print("已创建用户 {}（user_id={}）".format(user.username, user.user_id), file=out)
  return 0


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

  return parser


def main(argv=None) -> int:
  parser = build_parser()
  arguments = parser.parse_args(argv)

  if arguments.command == "create-user":
    ##
    ## Imported here rather than at module scope so that `--help` works, and
    ## the parser can be tested, without configuration or a database.
    ##
    from backend.src.library.configlib import load_config
    from backend.src.web.auth_routes import build_auth_runtime

    runtime = build_auth_runtime(load_config)
    return create_user_command(arguments.username, service_factory=runtime.service)

  parser.error("unknown command")
  return 2
