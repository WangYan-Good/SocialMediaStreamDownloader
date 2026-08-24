##
## The module ``python -m backend.src.auth_cli`` runs.
##
## A thin entry point beside the other modules rather than a console script, so
## it works from a checkout with no install step - which is how this project is
## deployed.
##
import sys

from backend.src.auth.cli import main


if __name__ == "__main__":
  sys.exit(main())
