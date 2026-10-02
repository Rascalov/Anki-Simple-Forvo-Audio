import threading
import urllib.parse

import requests

"""
The openrussian source (Russian only).

The dictionary at en.openrussian.org serves audio through a private API that
requires a logged-in session cookie:

    GET https://en.openrussian.org/_api/audio/ru/<word>?page=%2F

It always answers with a recording URL (real recordings where they exist,
synthesised TTS otherwise), so this source is deliberately used only as the
very last resort: the forga CDN and lingua libre are asked first, and only a
word neither of them has is sent here.

The session is taken from the config if it was pasted in there; otherwise the
configured login credentials are exchanged for a fresh session via
POST /_api/login. The session is cached for the lifetime of the process.

The aqt-dependent helpers are imported lazily so this module stays testable
without Anki, like resolver.py and normalize.py.
"""

OPENRUSSIAN_API = "https://en.openrussian.org/_api"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:156.0) "
    "Gecko/20100101 Firefox/156.0"
)

_session_lock = threading.Lock()
_session_cache = {"session": None}


def openrussian_lookup(value, language):
    """Audio from openrussian. Any language but Russian comes back empty,
    with no network touched."""
    if language.split("_")[-1] != "ru":
        return []
    session = get_session()
    if not session:
        print("OpenRussian: no session available (set credentials or a session in config)")
        return []
    url = OPENRUSSIAN_API + "/audio/ru/" + urllib.parse.quote(value) + "?page=%2F"
    try:
        response = requests.get(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/json, text/plain, */*",
                "Referer": "https://en.openrussian.org/",
                "Cookie": "session=" + session,
            },
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        if data.get("error"):
            print("OpenRussian: api error:", data["error"])
            return []
        result = data.get("result") or {}
        link = result.get("url")
        if not link:
            return []
        audioID = link.rstrip("/").split("/")[-1].split(".mp3")[0]
        from .AnkiAudioTools import AnkiAudioObject

        return [AnkiAudioObject(value, audioID, link)]
    except Exception as err:
        print(f"OpenRussian: lookup failed for {value!r}: {err}")
        return []


def login(username, password):
    """Exchange login credentials for a session string. None when it fails."""
    try:
        response = requests.post(
            OPENRUSSIAN_API + "/login",
            json={"email": username, "password": password},
            timeout=15,
        )
        if response.status_code != 200:
            print(f"OpenRussian: login rejected ({response.status_code})")
            return None
        for part in response.headers.get("Set-Cookie", "").split(","):
            name, _, value = part.strip().partition("=")
            if name == "session":
                return value.split(";")[0]
    except Exception as err:
        print(f"OpenRussian: login failed: {err}")
    return None


def get_session():
    """The configured session, or one obtained from the configured credentials."""
    with _session_lock:
        if _session_cache["session"]:
            return _session_cache["session"]
        from .AnkiAudioTools import getConfig

        config = getConfig() or {}
        session = str(config.get("openrussianSession", "") or "").strip()
        if not session:
            username = str(config.get("openrussianUsername", "") or "").strip()
            password = str(config.get("openrussianPassword", "") or "")
            if username and password:
                session = login(username, password)
        if session:
            _session_cache["session"] = session
        return session
