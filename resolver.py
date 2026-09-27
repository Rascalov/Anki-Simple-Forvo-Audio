from .normalize import HEADWORD, clean, segment_field

"""
Deciding which audio a note field should get.

The policy, in order of preference:

1. The headword (the first line of the field) is looked up whole. A multi-word
   headword like 'Не за что' or 'ни разу' exists on the CDN as one recording,
   and one recording of the phrase always beats several of its words.
2. If the headword is not there as a phrase, it is covered by the longest
   pieces that are: 'местная газета' -> 'местная' + 'газета'.
3. Every later line is looked up *whole only*. It is added if the CDN has it
   ('Спасибо', 'пенсионерка') and skipped if it does not. Example sentences
   from a textbook are essentially never on the CDN, and stitching one together
   out of seven speakers' words is worse than leaving it silent.

Nothing is capped: a field gets audio for every part of it the CDN has. A note
carrying a conjugation table therefore collects one recording per form.

The lookup function is injected, so this module needs neither aqt nor network.
"""

# Longest headword that is worth covering word by word. Past this it is a
# sentence wearing a headword's hat, and rule 3 applies instead.
DEFAULT_COVER_MAX_TOKENS = 6


class CachedLookup:
    """Wraps a lookup so a deck run asks the CDN about 'не' only once."""

    def __init__(self, lookup, max_entries=4096):
        self.lookup = lookup
        self.max_entries = max_entries
        self.cache = {}
        self.calls = 0
        self.hits = 0

    def __call__(self, value, language):
        key = (language, value.lower())
        if key in self.cache:
            self.hits += 1
            return self.cache[key]
        self.calls += 1
        try:
            results = self.lookup(value, language) or []
        except Exception as err:
            print(f"Lookup failed for {value!r}: {err}")
            results = []
        if len(self.cache) < self.max_entries:
            self.cache[key] = results
        return results


class Resolution:
    """What resolve() decided, and how much it cost."""

    def __init__(self):
        self.audios = []
        self.lookups = 0
        self.chosen_for = []

    def add(self, audio, phrase):
        self.audios.append(audio)
        self.chosen_for.append(phrase)

    def __repr__(self):
        return f"Resolution({self.chosen_for!r}, lookups={self.lookups})"


def resolve(
    field,
    language,
    lookup,
    cover_max_tokens=DEFAULT_COVER_MAX_TOKENS,
    fallback=None,
):
    """Pick audio for one field. `lookup(value, language)` returns a list."""
    resolution = Resolution()
    seen = set()
    memo = {}

    def ask(value):
        """One lookup, memoised within this note so retries are free."""
        key = value.lower()
        if key not in memo:
            memo[key] = lookup(value, language)
        return memo[key]

    def take(results, phrase):
        for audio in results:
            key = getattr(audio, "id", None) or getattr(audio, "link", None)
            if key in seen:
                continue
            seen.add(key)
            resolution.add(audio, phrase)
            return True
        return False

    segments = segment_field(field, language)
    for segment in segments:
        if take(ask(segment.text), segment.text):
            continue

        # Only a headword earns the word-by-word treatment.
        tokens = segment.tokens
        if segment.role != HEADWORD or not 1 < len(tokens) <= cover_max_tokens:
            continue
        for phrase in _cover(tokens, ask):
            take(ask(phrase), phrase)

    if not resolution.audios and fallback is not None and segments:
        # Only the headword, and only once the CDN has given up: the fallbacks
        # scrape web pages and a deck run must not turn into a crawl.
        try:
            take(fallback(segments[0].text, language), segments[0].text)
        except Exception as err:
            print(f"Fallback failed for {segments[0].text!r}: {err}")

    resolution.lookups = len(memo)
    return resolution


def _cover(tokens, ask):
    """Longest-first cover of a token run. Yields the phrases that exist."""
    start = 0
    while start < len(tokens):
        for length in range(len(tokens) - start, 0, -1):
            candidate = clean(" ".join(tokens[start:start + length]))
            if candidate and ask(candidate):
                yield candidate
                start += length
                break
        else:
            # Nothing starting here exists; drop the token and move on.
            start += 1
