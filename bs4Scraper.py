from bs4 import BeautifulSoup
import urllib.request
import urllib.parse
import requests
from requests.exceptions import HTTPError, Timeout, RequestException
from .AnkiAudioTools import AnkiAudioObject, AnkiAudioGlobals

"""
Audio sources.

The primary source is the "forga" CDN (AnkiAudioGlobals.FORGA_BASE_URL).
When the CDN has no results we fall back to external sources:
- lingua libre (open audio records, any language)
- openrussian (Russian only)
"""


def fetch_html(url):
    try:
        page = urllib.request.Request(url)
        infile = urllib.request.urlopen(page).read()
        data = infile.decode('UTF-8')
        return BeautifulSoup(data, "html.parser")
    except Exception as e:
        print(str(e))
        return None


def lookup_word_lingua_libre(word, languageCode):
    audioList = []
    wordEncoded = urllib.parse.quote(word)
    page = fetch_html("https://lingualibre.org/index.php?search=" + wordEncoded)
    if page is None:
        return audioList
    links = page.select("a[href^='/wiki/Q']")
    pattern = word + " | audio record - " + languageCode
    for link in links:
        clean_title = link["title"].replace("\u200E", "").lower()
        if clean_title.startswith(pattern):
            try:
                linkPage = fetch_html("https://lingualibre.org" + link['href'])
                wordID = link['href'][link['href'].find("Q"):]
                audioList.append(AnkiAudioObject(word, wordID, linkPage.select_one("source[type^='audio/ogg']")['src']))
            except Exception as e:
                print(str(e))
    return audioList


def scrape_yandex_tts(word):
    # Russian only (from en.openrussian.org)
    audioList = []
    url = f"https://api.openrussian.org/read/ru/{urllib.parse.quote(word)}"
    response = requests.get(url, allow_redirects=False)
    location = response.headers.get("Location")
    if not location:
        print(f"OpenRussian: no audio location for '{word}'")
        return audioList
    wordID = location.split('/')[-1].split('.mp3')[0]
    audioList.append(AnkiAudioObject(word, wordID, location))
    return audioList


def forga_lookup(word, language):
    """Look up audio on the forga CDN. `language` uses the full 'Language_code' format (e.g. 'English_en').

    The CDN matches exactly and case-insensitively, so `word` must already be
    normalized (see normalize.py). Results come back best-first."""
    print(f"Forga: looking up '{word}' in '{language}'")
    results = []
    try:
        response = requests.get(
            AnkiAudioGlobals.FORGA_BASE_URL + "/audios",
            params={"language": language, "value": word},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        for audio in data:
            results.append(AnkiAudioObject(word, audio['id'], audio['link']))
    except (HTTPError, Timeout, RequestException) as err:
        print(f"Forga: request failed: {err}")
    except ValueError as err:
        print(f"Forga: invalid response: {err}")
    except Exception as err:
        print(f"Forga: an error occurred: {err}")

    print(f"Forga: Results count: {len(results)}")
    return results
