##<<Third-part>>
from backend.src.platform.resource_resolution import (
  RESOURCE_TYPE_LIVE,
  RESOURCE_TYPE_OWNER,
  RESOURCE_TYPE_POST,
)


class OwnerDetailUnavailable(RuntimeError):
  """Nothing was wired to read a profile.

  Its own type so the failure names the wiring rather than surfacing as a
  ``None`` being called, which is what it used to look like.
  """


class DouyinOwnerIdentityReader:
  """Who is behind a douyin url that has *already* been named.

  A share link identifies an owner whichever kind it is - their profile, one of
  their posts, or their live room - so all three are read here, and the answer
  is always keyed on ``owner_user_id``.  The link itself is never an identity:
  douyin issues different short links for the same post, so matching on one
  would treat the same thing as two.

  Nothing here follows anything.  Every entry point takes a url that has already
  been resolved - by ``/api/resolve``, which has the scheme, host, loop and hop
  checks that make following one safe, or by the owner runtime's own single
  hop.  A second follow here would repeat that decision in a place with none of
  those checks, and repeat the request that made it.

  One implementation, reached two ways.  ``from_resolution`` serves the receipt
  path and ``from_resolved_url`` the link path; both land on the same three
  readers, so the two cannot come to disagree about what a post link means.
  """

##
## >>============================= private method =============================>>
##
  def __init__(
    self,
    owner_detail=None,
    post_resolution=None,
    live_probe=None,
  ) -> None:
    ##
    ## Injected rather than reached for, so a test proves what was *not*
    ## requested as easily as what was.
    ##
    self._owner_detail = owner_detail
    self._post_resolution = post_resolution
    self._live_probe = live_probe

  def _from_profile(self, sec_user_id: str):
    """The profile is where ``uid`` comes from; the receipt carries only the
    sec id, and ``person_account`` is keyed on the uid."""
    if self._owner_detail is None:
      raise OwnerDetailUnavailable("no owner profile reader is wired")
    owner = self._owner_detail(sec_user_id)
    if owner is None:
      return None
    return {
      "owner_user_id": (getattr(owner, "uid", "") or "").strip(),
      "sec_user_id": getattr(owner, "sec_user_id", None) or sec_user_id,
      "nickname": getattr(owner, "nickname", None),
    }

  def _from_post(self, url: str, aweme_id: str):
    """The post payload already carries the author's id, sec id and nickname,
    so resolving the post answers the whole question - no second request for
    the profile."""
    resolution = self._post_resolver()(url, aweme_id=aweme_id)
    if not getattr(resolution, "ok", False) or resolution.detail is None:
      return None
    detail = resolution.detail
    return {
      "owner_user_id": (getattr(detail, "owner_user_id", "") or "").strip(),
      "sec_user_id": getattr(detail, "sec_user_id", None),
      "nickname": getattr(detail, "nickname", None),
    }

  def _from_live(self, url: str):
    """Open or not.  The probe reports the room's owner either way, so a marked
    owner does not have to be streaming at the moment you mark them."""
    probe = self._live_prober()(url)
    owner_user_id = (getattr(probe, "owner_user_id", "") or "").strip()
    if not owner_user_id:
      return None
    return {
      "owner_user_id": owner_user_id,
      "sec_user_id": getattr(probe, "sec_user_id", None),
      "nickname": getattr(probe, "nickname", None),
    }

  def _post_resolver(self):
    if self._post_resolution is not None:
      return self._post_resolution

    ##
    ## The process-wide downloader, imported here rather than at module scope:
    ## it builds a platform client, and merely being able to name an owner must
    ## not cost that.
    ##
    def resolve(url, aweme_id=None):
      from backend.src.platform.douyin.douyin_aweme_downloader import (
        get_aweme_downloader,
      )

      return get_aweme_downloader().resolver.resolve(url, aweme_id=aweme_id)

    return resolve

  def _live_prober(self):
    if self._live_probe is not None:
      return self._live_probe

    def probe(url):
      from backend.src.platform.douyin.douyin_live_downloader import (
        get_live_downloader,
      )

      return get_live_downloader().prober.probe(url)

    return probe

##
## >>============================= sub class method =============================>>
##
  def from_resolution(self, resolution):
    """Read the owner named by a resolution this server issued, or ``None``.

    Dispatches on ``resource_type`` rather than re-reading the url, because
    that verdict is the server's own and was reached with checks this class
    does not repeat.  ``resolved_url`` is what the readers are given: the short
    link has already been followed, once, safely.
    """
    resource_type = getattr(resolution, "resource_type", None)
    resolved_url = getattr(resolution, "resolved_url", None) or ""
    identity = dict(getattr(resolution, "identity", None) or {})

    if resource_type == RESOURCE_TYPE_OWNER:
      sec_user_id = identity.get("sec_user_id")
      if not sec_user_id:
        return None
      return self._from_profile(sec_user_id)

    if resource_type == RESOURCE_TYPE_POST:
      aweme_id = identity.get("aweme_id")
      if not aweme_id:
        return None
      return self._from_post(resolved_url, aweme_id)

    if resource_type == RESOURCE_TYPE_LIVE:
      ##
      ## A live receipt carries no identity on purpose - the number in
      ## ``live.douyin.com/123`` is the room's *web* id, not the ``room_id``
      ## every table uses - so the room is the only thing there is to ask.
      ##
      return self._from_live(resolved_url)

    return None

  def from_resolved_url(self, url: str):
    """Read the owner out of a url that has already been followed, or ``None``.

    The url is classified here because this entry point has no verdict handed
    to it.  Profile first, then post, then the live hosts - the same order the
    owner path has always used.
    """
    if not isinstance(url, str) or not url.strip():
      return None

    from backend.src.platform.douyin.douyin_owner_url import classify_owner_url

    sec_user_id = classify_owner_url(url)
    if sec_user_id is not None:
      return self._from_profile(sec_user_id)

    from backend.src.platform.douyin.douyin_aweme_url import classify_aweme_url

    aweme_id = classify_aweme_url(url)
    if aweme_id is not None:
      return self._from_post(url, aweme_id)

    from backend.src.platform.douyin.douyin_url_hosts import (
      host_of,
      is_live_host,
    )

    if is_live_host(host_of(url)):
      return self._from_live(url)
    return None
