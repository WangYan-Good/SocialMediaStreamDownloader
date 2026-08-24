##<<Base>>
import io
import unittest

##<<Third-part>>
from backend.src.auth.cli import create_user_command
from backend.src.auth.errors import AuthUnavailable, DuplicateUsername
from backend.src.auth.service import AuthenticationService
from backend.src.unit_test.test_auth_service import FakeRepository


##
## >>============================= why a CLI at all =============================>>
##
##
## There is no sign-up endpoint, deliberately: nothing is owned by anybody yet
## and no endpoint checks permissions, so a self-service account would be an
## account that can already see everything.  Until ownership and authorization
## exist, an account is something whoever runs the deployment creates on
## purpose - which is what this is.
##


def run(
  username="alice",
  passwords=("correct horse battery", "correct horse battery"),
  repository=None,
  service=None,
):
  """Drive the command with the prompts injected rather than typed."""
  repository = repository if repository is not None else FakeRepository()
  service = service or AuthenticationService(repository, session_ttl_seconds=3600)
  output = io.StringIO()
  answers = list(passwords)

  code = create_user_command(
    username,
    service_factory=lambda: service,
    prompt=lambda _label: answers.pop(0),
    out=output,
  )
  return code, output.getvalue(), repository


class TestCreatingAnAccount(unittest.TestCase):
  def test_it_creates_the_account(self):
    code, _, repository = run()

    self.assertEqual(0, code)
    self.assertEqual("alice", repository.users[1]["username"])

  def test_it_asks_twice_and_refuses_a_mismatch(self):
    ##
    ## A typo in a password nobody can see is otherwise discovered at the first
    ## failed login, by which point nobody knows what was actually typed.
    ##
    code, output, repository = run(passwords=("first password", "second password"))

    self.assertNotEqual(0, code)
    self.assertEqual({}, repository.users)
    self.assertIn("两次输入的密码不一致", output)

  def test_it_never_prints_the_password(self):
    ##
    ## The reason ``prompt`` is getpass in production: a password echoed to the
    ## terminal ends up in a scrollback buffer, and one passed as an argument
    ## ends up in shell history and in ps.
    ##
    secret = "correct horse battery"
    _, output, _ = run(passwords=(secret, secret))

    self.assertNotIn(secret, output)

  def test_it_never_prints_the_hash(self):
    _, output, repository = run()

    self.assertNotIn(repository.users[1]["password_hash"], output)
    self.assertNotIn("scrypt", output)

  def test_it_refuses_a_password_that_is_too_short(self):
    code, output, repository = run(passwords=("short", "short"))

    self.assertNotEqual(0, code)
    self.assertEqual({}, repository.users)
    self.assertIn("密码", output)

  def test_it_refuses_a_name_that_is_already_taken(self):
    repository = FakeRepository()
    service = AuthenticationService(repository, session_ttl_seconds=3600)
    run(repository=repository, service=service)

    code, output, _ = run(username="ALICE", repository=repository, service=service)

    self.assertNotEqual(0, code)
    self.assertIn("已存在", output)

  def test_it_refuses_an_empty_name(self):
    code, _, repository = run(username="   ")

    self.assertNotEqual(0, code)
    self.assertEqual({}, repository.users)

  def test_it_says_so_when_the_database_cannot_be_reached(self):
    ##
    ## Including when the schema is behind the code: creating an account writes
    ## to a table that migration 0007 introduces, so a database still on 0006
    ## has nowhere to put it.
    ##
    def failing():
      raise AuthUnavailable("schema is behind")

    output = io.StringIO()
    code = create_user_command(
      "alice",
      service_factory=failing,
      prompt=lambda _label: "correct horse battery",
      out=output,
    )

    self.assertNotEqual(0, code)
    self.assertIn("认证服务暂时不可用", output.getvalue())

  def test_an_internal_reason_is_not_printed_verbatim(self):
    def failing():
      raise AuthUnavailable("pymysql OperationalError 2003 connect refused")

    output = io.StringIO()
    create_user_command(
      "alice",
      service_factory=failing,
      prompt=lambda _label: "correct horse battery",
      out=output,
    )

    for internal in ("pymysql", "OperationalError", "2003"):
      self.assertNotIn(internal, output.getvalue())


class TestTheCommandLineSurface(unittest.TestCase):
  def test_there_is_no_way_to_pass_a_password_as_an_argument(self):
    ##
    ## A password in argv is a password in shell history, in ps output for
    ## every user on the box, and in any CI log that echoes its commands.
    ##
    from backend.src.auth import cli

    parser = cli.build_parser()
    known = {action.dest for action in parser._actions}

    self.assertNotIn("password", known)



class TestInterruptedInput(unittest.TestCase):
  def test_a_cancelled_prompt_is_a_message_rather_than_a_traceback(self):
    ##
    ## Ctrl-C, Ctrl-D, or the command run with no terminal attached - a script,
    ## a pipeline, a CI step that did not expect to be asked. A traceback here
    ## is noise that looks like a crash.
    ##
    def cancelled(_label):
      raise EOFError()

    output = io.StringIO()
    repository = FakeRepository()
    service = AuthenticationService(repository, session_ttl_seconds=3600)

    code = create_user_command(
      "alice",
      service_factory=lambda: service,
      prompt=cancelled,
      out=output,
    )

    self.assertNotEqual(0, code)
    self.assertIn("已取消", output.getvalue())
    self.assertNotIn("Traceback", output.getvalue())
    self.assertEqual({}, repository.users)

  def test_an_interrupt_is_handled_the_same_way(self):
    def interrupted(_label):
      raise KeyboardInterrupt()

    output = io.StringIO()
    code = create_user_command(
      "alice",
      service_factory=lambda: AuthenticationService(
        FakeRepository(), session_ttl_seconds=3600
      ),
      prompt=interrupted,
      out=output,
    )

    self.assertNotEqual(0, code)
    self.assertIn("已取消", output.getvalue())

if __name__ == "__main__":
  unittest.main()
