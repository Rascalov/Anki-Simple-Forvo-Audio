from .AnkiAudioTools import configBool
from .bs4Scraper import forga_lookup, lookup_word_lingua_libre
from .normalize import clean, normalize
from .openrussian import openrussian_lookup

"""
Audio acquisition.

The forga CDN is the only real source. It matches exactly, so everything asked
of it goes through `normalize` first: Russian stress marks off, French accents
kept, glosses and edge punctuation gone.

When the CDN has nothing we fall back to external sources (lingua libre for any
language, openrussian for Russian), but only with "Use fallback sources" on.

Openrussian always answers for Russian (synthesising audio where no recording
exists), so it sits at the very end of the chain. The manual search dialog
presents it only when nothing else matched, and the automated deck run leaves
it out unless the "Use openrussian for automated audio insertion" config
option is turned on.

Splitting a phrase into words is not done here; `resolver` owns that decision.
"""


def cdn_lookup(value, language):
    """The primary source. `language` is 'Name_code', e.g. 'English_en'."""
    return forga_lookup(value, language)


def fallback_lookup(value, language):
    """External sources, used only once the CDN has come up empty.

    Lingua libre first, openrussian last for Russian: openrussian generates
    audio for anything, so it must never shadow a real recording.
    """
    if not configBool("Use fallback sources"):
        return []
    languageCode = language.split("_")[-1]
    results = lookup_word_lingua_libre(value, languageCode)
    if not results and languageCode == "ru":
        results = openrussian_lookup(value, language)
    return results


def automated_fallback_lookup(value, language):
    """The fallback chain for the automated deck run.

    Lingua libre only: openrussian is opt-in for the automated run, enabled by
    the dialog's checkbox and fed to the resolver as a gap filler, so it covers
    what the CDN missed instead of waiting for the whole field to come up
    empty.
    """
    if not configBool("Use fallback sources"):
        return []
    return lookup_word_lingua_libre(value, language.split("_")[-1])


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
