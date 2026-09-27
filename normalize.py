import html
import re
import unicodedata

"""
Turning an Anki field into things the CDN can actually be asked about.

The CDN matches exactly (case-insensitively) and does nothing else: no
substring search, no fuzzy matching, no diacritic folding. So the whole job
here is producing a *literal* spelling that the source data is likely to use.

A field is not one query. `Не р<u>а</u>з (= много раз)<br>Мы не раз ходили в
это кафе.` is a headword, a gloss to throw away, and an example sentence. This
module cuts a field into ordered segments and labels the first line's segments
as headwords, because that is the part worth insisting on.

Nothing here imports aqt, so it can be tested without Anki.
"""

# Languages whose learning materials mark stress with a combining acute/grave
# that is not part of the spelling. Latin/Greek scripts are deliberately absent:
# there an acute is orthography (French 'élève', Spanish 'está') and stripping
# it would turn a hit into a miss.
STRESS_MARKS = ("́", "̀")
CYRILLIC_RANGES = ((0x0400, 0x04FF), (0x0500, 0x052F), (0x2DE0, 0x2DFF), (0xA640, 0xA69F))

SOUND_TAG_RE = re.compile(r"\[sound:[^\]]*\]")
# Block-level tags are line breaks; inline tags are not. Deleting <u> with a
# space turns the stress markup 'Н<u>е</u>когда' into 'Н е когда'.
BLOCK_TAG_RE = re.compile(r"(?i)</?(?:br|div|p|li|tr|td|th|h[1-6]|table|thead|tbody|ul|ol|dl|dt|dd|blockquote|hr|section)\b[^>]*>")
INLINE_TAG_RE = re.compile(r"<[^>]*>")
# Glosses and grammar notes: '(= много раз)', '(ontelbaar)', '(m)', '(+пред.)'.
BRACKET_PAIRS = {"(": ")", "[": "]", "{": "}"}
# Aspect pairs and alternatives: 'решать – решить', 'убивать/убить время'.
# A spaced hyphen separates; an unspaced one does not, or 'по-русски' would split.
ALTERNATIVES_RE = re.compile(r"\s+[/–—|]\s+|\s+-\s+|\s*/\s*")
WORD_RE = re.compile(r"\w+", re.UNICODE)

EDGE_PUNCTUATION = " \t .,;:!?…\"'«»„“”‘’()[]{}-–—*·•"

HEADWORD = "headword"
EXTRA = "extra"


class Segment:
    """One lookup candidate, with where in the field it came from."""

    def __init__(self, text, role, line):
        self.text = text
        self.role = role
        self.line = line

    @property
    def tokens(self):
        return tokenize(self.text)

    def __eq__(self, other):
        return (self.text, self.role, self.line) == (other.text, other.role, other.line)

    def __repr__(self):
        return f"Segment({self.text!r}, {self.role}, line={self.line})"


def is_cyrillic(char):
    point = ord(char)
    return any(low <= point <= high for low, high in CYRILLIC_RANGES)


def strip_stress_marks(text):
    """Drop a combining acute/grave that sits on a Cyrillic letter.

    'ме́сто' -> 'место' (the CDN has no entry with the mark), while 'élève' and
    'está' are left alone. 'ё' and 'й' survive because only the two stress marks
    are dropped and the result is recomposed.
    """
    decomposed = unicodedata.normalize("NFD", text)
    kept = []
    for char in decomposed:
        if char in STRESS_MARKS and kept and is_cyrillic(kept[-1]):
            continue
        kept.append(char)
    return unicodedata.normalize("NFC", "".join(kept))


def normalize_caps_stress(text):
    """'очкОв' -> 'очков'. Lowercase a capital sitting inside a lowercase word.

    The CDN lowercases the query anyway, so this only keeps the downloaded
    filename tidy. Words that start with a capital ('МГУ', 'Москва') are left
    alone.
    """

    def fix(match):
        word = match.group(0)
        if word[:1].islower() and word[1:] != word[1:].lower():
            return word.lower()
        return word

    return WORD_RE.sub(fix, text)


def normalize(text, language):
    """Apply the language's spelling policy to a piece of text."""
    text = unicodedata.normalize("NFC", text)
    if uses_stress_marks(language):
        text = strip_stress_marks(text)
        text = normalize_caps_stress(text)
    return text


def uses_stress_marks(language):
    """True when the language writes pedagogical stress marks over its letters."""
    code = language.split("_")[-1]
    return code in ("ru", "uk", "be", "bg", "mk", "sr", "rue")


def to_lines(field):
    """Anki field HTML -> visual lines, sound tags and markup removed."""
    text = SOUND_TAG_RE.sub(" ", field)
    # A newline in the source is whitespace, not a break. Pasted conjugation
    # tables are full of them: 'он\n\tприходит' is one cell, not two lines.
    text = re.sub(r"[\r\n\t]+", " ", text)
    text = BLOCK_TAG_RE.sub("\n", text)
    text = INLINE_TAG_RE.sub("", text)
    text = html.unescape(text)
    text = text.replace(" ", " ")
    lines = (re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n"))
    return [line for line in lines if line]


def strip_bracketed(text):
    """Remove anything in brackets: glosses, grammar notes, translations.

    '(= много раз)', '(ontelbaar)', '(m)', '(+пред.)' are notes to the reader,
    never something to pronounce. Scanned rather than matched with a regex so
    that nesting ('слово (betekenis (extra))') and an unclosed bracket, which
    swallows the rest of the line, are both handled.
    """
    kept = []
    closers = []
    for char in text:
        if char in BRACKET_PAIRS:
            closers.append(BRACKET_PAIRS[char])
        elif closers:
            if char == closers[-1]:
                closers.pop()
                kept.append(" ")
        else:
            kept.append(char)
    return "".join(kept)


def clean(text):
    """Strip glosses, edge punctuation and repeated whitespace."""
    text = strip_bracketed(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text.strip(EDGE_PUNCTUATION).strip()


def tokenize(text):
    return [token for token in text.split() if token.strip(EDGE_PUNCTUATION)]


def segment_field(field, language):
    """Field HTML -> ordered Segments, deduplicated, headwords first.

    Every segment cut from the first non-empty line is a headword: that is the
    word the card is about. Later lines are extras (example sentences, other
    inflections, conjugation tables).
    """
    segments = []
    have_headword = False
    for index, line in enumerate(to_lines(field)):
        # Brackets go first, before the line is cut anywhere. A separator
        # inside an aside ('мочь (kunnen / mogen)') would otherwise split the
        # line at a slash that is not an aspect pair, leaving the halves of the
        # gloss unbracketed and looking like words.
        line = re.sub(r"\s+", " ", strip_bracketed(line)).strip()
        if not line:
            continue
        # 'Будущее время:' heads a conjugation table, it is not a word to say.
        # Only checked once a headword exists, so one can never be lost here.
        if have_headword and line.endswith(":"):
            continue
        role = HEADWORD if not have_headword else EXTRA
        # Splitting on '/' is an aspect-pair rule, so it only applies to the
        # headword. On a later line a slash is usually a pronoun list:
        # 'он/она/оно зайдёт' is one form, not three words to pronounce.
        parts = ALTERNATIVES_RE.split(line) if role == HEADWORD else [line]
        for part in parts:
            text = clean(normalize(part, language))
            if text:
                segments.append(Segment(text, role, index))
                have_headword = True

    seen = set()
    unique = []
    for segment in segments:
        key = segment.text.lower()
        if key not in seen:
            seen.add(key)
            unique.append(segment)
    return unique
