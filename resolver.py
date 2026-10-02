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

An opt-in `gap_filler` narrows rule 2: when it is set, only a two-word
segment the CDN does not have whole may still be stitched from its words,
with the missing one filled in from the filler. Anything longer is taken
from it as one piece. It is never asked about anything the CDN delivered.

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
    gap_filler=None,
):
    """Pick audio for one field. `lookup(value, language)` returns a list.

    `gap_filler` is an opt-in source that covers what the primary source
    missed: a two-word segment not on the CDN whole may still be stitched
    from its words (the missing one filled in from the filler), and any
    longer segment is taken from it as one piece. It is never consulted for
    anything the primary source delivered.
    """
    resolution = Resolution()
    seen = set()
    memo = {}
    gap_memo = {}

    def ask(value):
        """One primary-source lookup, memoised within this note so retries are free."""
        key = value.lower()
        if key not in memo:
            memo[key] = lookup(value, language)
        return memo[key]

    def fill(value):
        """One gap-filler lookup, memoised so a repeated missing word asks once."""
        key = value.lower()
        if key not in gap_memo:
            gap_memo[key] = gap_filler(value, language)
        return gap_memo[key]

    def take_piece(results, phrase):
        """The first recording of `results` not already taken, or None."""
        for audio in results:
            key = getattr(audio, "id", None) or getattr(audio, "link", None)
            if key in seen:
                continue
            seen.add(key)
            return audio
        return None

    segments = segment_field(field, language)
    for segment in segments:
        # (token offset, audio, phrase) pieces of this segment, kept in reading
        # order so the audios play left to right regardless of which source
        # delivered them.
        pieces = []

        whole = take_piece(ask(segment.text), segment.text)
        if whole is not None:
            pieces.append((0, whole, segment.text))
        else:
            tokens = segment.tokens
            if gap_filler is not None:
                # With the filler enabled only a two-word segment is still
                # stitched from its words; anything longer is taken from the
                # filler as one piece instead of being built out of single
                # speakers.
                fragment = len(tokens) == 2
            else:
                fragment = (
                    segment.role == HEADWORD and 1 < len(tokens) <= cover_max_tokens
                )
            if fragment:
                covered = set()
                start = 0
                while start < len(tokens):
                    for length in range(len(tokens) - start, 0, -1):
                        candidate = clean(" ".join(tokens[start:start + length]))
                        results = ask(candidate) if candidate else []
                        if results:
                            audio = take_piece(results, candidate)
                            if audio is not None:
                                pieces.append((start, audio, candidate))
                            covered.update(range(start, start + length))
                            start += length
                            break
                    else:
                        # Nothing starting here exists; drop the token.
                        start += 1

                if gap_filler is not None:
                    if covered:
                        # Some words were found: the filler adds the rest,
                        # each at its own position in the phrase.
                        for i, token in enumerate(tokens):
                            if i in covered:
                                continue
                            audio = take_piece(fill(token), token)
                            if audio is not None:
                                pieces.append((i, audio, token))
                    else:
                        # Neither word was found: take the pair whole from
                        # the filler instead of two openrussian words.
                        audio = take_piece(fill(segment.text), segment.text)
                        if audio is not None:
                            pieces.append((0, audio, segment.text))
            elif gap_filler is not None:
                audio = take_piece(fill(segment.text), segment.text)
                if audio is not None:
                    pieces.append((0, audio, segment.text))

        for _, audio, phrase in sorted(pieces, key=lambda piece: piece[0]):
            resolution.add(audio, phrase)

    if not resolution.audios and fallback is not None and segments:
        # Only the headword, and only once nothing at all was found: the
        # fallbacks scrape web pages and a deck run must not turn into a crawl.
        try:
            audio = take_piece(fallback(segments[0].text, language), segments[0].text)
            if audio is not None:
                resolution.add(audio, segments[0].text)
        except Exception as err:
            print(f"Fallback failed for {segments[0].text!r}: {err}")

    resolution.lookups = len(memo)
    return resolution
