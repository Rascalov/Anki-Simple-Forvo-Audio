from .AnkiAudioTools import configBool
from .bs4Scraper import forga_lookup, lookup_word_lingua_libre, scrape_yandex_tts
from .normalize import clean, normalize

"""
Audio acquisition.

The forga CDN is the only real source. It matches exactly, so everything asked
of it goes through `normalize` first: Russian stress marks off, French accents
kept, glosses and edge punctuation gone.

When the CDN has nothing we fall back to external sources (lingua libre for any
language, openrussian for Russian), but only with "Use fallback sources" on.
Splitting a phrase into words is not done here; `resolver` owns that decision.
"""


def cdn_lookup(value, language):
    """The primary source. `language` is 'Name_code', e.g. 'English_en'."""
    return forga_lookup(value, language)


def fallback_lookup(value, language):
    """External sources, used only once the CDN has come up empty."""
    if not configBool("Use fallback sources"):
        return []
    languageCode = language.split("_")[-1]
    results = lookup_word_lingua_libre(value, languageCode)
    if not results and languageCode == "ru":
        results = scrape_yandex_tts(value)
    return results


def getAudioSources(word, language):
    """Look up a single phrase, CDN first then fallbacks.

    This is the manual search path (the editor dialog), where the user typed or
    selected exactly what they want and every result is worth showing.
    """
    value = clean(normalize(word, language)) or word.strip()
    results = cdn_lookup(value, language)
    if results:
        return results
    return fallback_lookup(value, language)
