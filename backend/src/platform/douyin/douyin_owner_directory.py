##<<Base>>
##
## Owner folder naming, shared by the live and post paths.
##
## Both paths file downloads under a folder named after the owner, and both hit the
## same two problems doing it.  The policy lives here as pure functions so the two
## cannot drift apart; each path fetches its own inputs from its own database
## handle and passes them in.
##
## Problem 1 - a nickname is only today's nickname.  An owner who renames
## themselves would get a second folder, splitting their history.  Both paths
## already read the recorded folder from share_url for this reason.
##
## Problem 2 - a nickname does not identify an owner.  Douyin lets different
## accounts hold the same one, so several owners share a folder and their files sit
## mixed together.  Measured on this database: 39 folder names cover more than one
## owner, four of them cover three.
##

##
## Hard limit on one path component, in bytes rather than characters; see
## douyin_aweme_external_info.MAX_FILE_NAME_BYTES for the measurement.
## share_url.directory_name is VARCHAR(100), and 100 CJK characters are 300 bytes,
## so the column permits more than a path component can hold.
##
MAX_DIRECTORY_NAME_BYTES = 255


def fit_directory_name(name: str, suffix: str = "") -> str:
  """Hold a folder name within the per-component byte limit.

  ``suffix`` is kept whole and the name is trimmed to make room, so a
  discriminator is never the part that gets dropped.  Trimming lands on a
  character boundary rather than splitting a multi-byte character.
  """
  if not name:
    return suffix
  budget = MAX_DIRECTORY_NAME_BYTES - len(suffix.encode("utf-8"))
  if budget <= 0:
    return suffix
  encoded = name.encode("utf-8")
  if len(encoded) <= budget:
    return name + suffix
  return encoded[:budget].decode("utf-8", errors="ignore") + suffix


def choose_owner_directory(
  nickname_directory: str,
  recorded_directory: str = None,
  owner_user_id: str = None,
  owner_count: int = 1,
  person_directory: str = None,
) -> str:
  """Return the folder name to use for one owner.

  ``nickname_directory`` is the sanitised nickname from the current payload.
  ``recorded_directory`` is what share_url already holds for this owner, which
  wins when present - that is what keeps a renamed owner in one folder.
  ``owner_count`` is how many distinct owners share the chosen name; above one, the
  owner id is appended.

  The discriminator is applied to *every* owner in a colliding group, including
  whoever was downloaded first, so the layout on disk does not depend on download
  order.

  ``person_directory`` is the folder a marked person files under, and it wins
  outright - it is the only one of the three a human named on purpose.  An
  account nobody marked passes ``None`` here and the result is unchanged.
  """
  ##
  ## Taken before the discriminator, and returned without it.  The suffix
  ## disambiguates *accounts* that would otherwise collide; applied to a person
  ## folder it would give the same person's two accounts
  ## ``name_<account A>`` and ``name_<account B>`` - splitting apart exactly what
  ## marking them was meant to join.  A folder someone named on purpose needs no
  ## disambiguation.
  ##
  if isinstance(person_directory, str) and person_directory.strip():
    return fit_directory_name(person_directory)

  chosen = recorded_directory or nickname_directory or ""
  if not chosen:
    return ""
  if owner_count > 1 and owner_user_id:
    return fit_directory_name(chosen, "_" + str(owner_user_id))
  return fit_directory_name(chosen)
