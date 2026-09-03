##
## The module ``python -m backend.src.recording_orphan_cli`` runs.
##
## A thin entry point beside the other commands rather than a console script, so
## it works from a checkout with no install step - which is how this project is
## deployed, and how ``backend.src.auth_cli`` already works.
##
import sys

from backend.src.service.recording_orphan_cli import main


if __name__ == "__main__":
  sys.exit(main())
