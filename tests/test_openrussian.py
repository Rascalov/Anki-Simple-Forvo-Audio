# pyright: reportMissingImports=false
"""The openrussian source: Russian-only gate, session handling, parsing.

The source imports the aqt-dependent `getConfig` lazily, so it can be tested
by stubbing `forvo_addon.AnkiAudioTools` in sys.modules and by swapping in a
fake `requests`. No network is touched.
"""

import sys
import types
import unittest

import _bootstrap  # noqa: F401  (registers the add-on as an importable package)
from forvo_addon import openrussian

RU = "Russian_ru"
EN = "English_en"
AUDIO_URL = "https://s3.example/audio/x/abc123.mp3"


class FakeResponse:
    def __init__(self, payload=None, headers=None, status_code=200):
        self._payload = payload
        self.headers = headers or {}
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"http {self.status_code}")

    def json(self):
        return self._payload


class FakeRequests:
    def __init__(self):
        self.get_calls = []
        self.post_calls = []
        self.get_result = None
        self.post_result = None

    def get(self, url, **kwargs):
        self.get_calls.append((url, kwargs))
        return self.get_result

    def post(self, url, **kwargs):
        self.post_calls.append((url, kwargs))
        return self.post_result


def install_config(**values):
    """Point openrussian's lazy `from .AnkiAudioTools import ...` at a stub."""
    previous = sys.modules.get("forvo_addon.AnkiAudioTools")

    class AudioObject:
        def __init__(self, word, id, link):
            self.word = word
            self.id = id
            self.link = link

    mod = types.ModuleType("forvo_addon.AnkiAudioTools")
    mod.getConfig = lambda: dict(values)
    mod.AnkiAudioObject = AudioObject
    sys.modules["forvo_addon.AnkiAudioTools"] = mod
    return previous


def restore_config(previous):
    if previous is None:
        sys.modules.pop("forvo_addon.AnkiAudioTools", None)
    else:
        sys.modules["forvo_addon.AnkiAudioTools"] = previous


class OpenRussianTest(unittest.TestCase):
    def setUp(self):
        openrussian._session_cache["session"] = None
        self.fake = FakeRequests()
        openrussian.requests = self.fake
        self.fake.get_result = FakeResponse(
            {
                "result": {"lang": "ru", "text": "привет", "url": AUDIO_URL},
                "error": None,
            }
        )
        self.previous = None

    def tearDown(self):
        openrussian._session_cache["session"] = None
        restore_config(self.previous)


class TestRussianOnly(OpenRussianTest):
    def test_non_russian_is_skipped_without_network(self):
        self.previous = install_config(openrussianSession="s")
        self.assertEqual(openrussian.openrussian_lookup("hello", EN), [])
        self.assertEqual(self.fake.get_calls, [])

    def test_russian_makes_one_request(self):
        self.previous = install_config(openrussianSession="s")
        results = openrussian.openrussian_lookup("привет", RU)
        self.assertEqual(len(results), 1)
        self.assertEqual(len(self.fake.get_calls), 1)


class TestSession(OpenRussianTest):
    def test_no_session_and_no_credentials_returns_empty(self):
        self.previous = install_config()
        self.assertEqual(openrussian.openrussian_lookup("привет", RU), [])
        self.assertEqual(self.fake.get_calls, [])

    def test_configured_session_is_sent_as_cookie(self):
        self.previous = install_config(openrussianSession="sess123")
        openrussian.openrussian_lookup("привет", RU)
        url, kwargs = self.fake.get_calls[0]
        self.assertIn("/_api/audio/ru/", url)
        self.assertIn("session=sess123", kwargs["headers"]["Cookie"])

    def test_login_used_when_no_session_is_configured(self):
        self.previous = install_config(
            openrussianUsername="user@example.com", openrussianPassword="pw"
        )
        self.fake.post_result = FakeResponse(
            headers={"Set-Cookie": "session=sessFromLogin; Max-Age=3600"}
        )
        results = openrussian.openrussian_lookup("привет", RU)
        self.assertEqual(len(results), 1)
        self.assertEqual(len(self.fake.post_calls), 1)
        url, kwargs = self.fake.post_calls[0]
        self.assertTrue(url.endswith("/_api/login"))
        self.assertEqual(kwargs["json"]["email"], "user@example.com")

    def test_session_is_cached_across_lookups(self):
        self.previous = install_config(
            openrussianUsername="user@example.com", openrussianPassword="pw"
        )
        self.fake.post_result = FakeResponse(headers={"Set-Cookie": "session=sessFromLogin"})
        openrussian.openrussian_lookup("привет", RU)
        openrussian.openrussian_lookup("пока", RU)
        self.assertEqual(len(self.fake.post_calls), 1)

    def test_failed_login_yields_no_results(self):
        self.previous = install_config(
            openrussianUsername="user@example.com", openrussianPassword="bad"
        )
        self.fake.post_result = FakeResponse(headers={}, status_code=400)
        self.assertEqual(openrussian.openrussian_lookup("привет", RU), [])
        self.assertEqual(self.fake.get_calls, [])


class TestParsing(OpenRussianTest):
    def test_api_error_payload_yields_no_results(self):
        self.previous = install_config(openrussianSession="s")
        self.fake.get_result = FakeResponse(
            {"result": None, "error": {"code": 500, "message": "boom"}}
        )
        self.assertEqual(openrussian.openrussian_lookup("привет", RU), [])

    def test_missing_url_yields_no_results(self):
        self.previous = install_config(openrussianSession="s")
        self.fake.get_result = FakeResponse(
            {"result": {"lang": "ru", "text": "привет", "url": None}, "error": None}
        )
        self.assertEqual(openrussian.openrussian_lookup("привет", RU), [])

    def test_result_is_an_audio_object_with_a_stable_id(self):
        self.previous = install_config(openrussianSession="s")
        (audio,) = openrussian.openrussian_lookup("привет", RU)
        self.assertEqual(audio.id, "abc123")
        self.assertEqual(audio.link, AUDIO_URL)


if __name__ == "__main__":
    unittest.main()
