# Changelog

## 2.0.0

The add-on no longer scrapes forvo.com. Audio comes from the
[forga](https://forga.charitycook.com) CDN, and the auto-fetch understands the
shape of a card instead of treating a field as one long string.

### Removed

* **Direct forvo.com scraping.** `lookup_word`, `lookup_words`,
  `scrapeAnkiAudioObject`, `get_forvo_page`, `get_audio_link`, `remove_noise`
  and the language-list scraper are gone, along with the request counter and
  the "Maximum Forvo Downloads reached" handling that existed to stay under
  forvo's rate limit.
* **The "Acquisition method" radio buttons** ("CDN + Forvo as Backup" / "Only
  Forvo (Broken)") and `AcquisitionType`. There is one pipeline now.
* **Config `MaxForvoDownloads`** — nothing is rate limited any more.
* **Config `ignorePunctuation`** — punctuation is now handled per language
  instead of being stripped wholesale. The old setting destroyed `по-русски`
  and `c'est`, which the CDN files under exactly those spellings.

### Added

* **`normalize.py`** — turns a field into ordered lookup candidates. Block tags
  become line breaks, inline tags do not, HTML entities and `[sound:…]` tags
  are dropped, and aspect pairs written `решать – решить` or `убивать/убить`
  become separate headwords.
* **Anything in brackets is ignored.** `(= много раз)`, `(ontelbaar)`, `(m)`,
  `(+пред.)`, `[note]` and `{aside}` are notes to the reader, not something to
  pronounce. Brackets are removed before the line is split anywhere, so a
  separator inside an aside — `мочь (kunnen / mogen)` — no longer cuts the line
  at a slash that was never an aspect pair. Nesting and an unclosed bracket
  (which swallows the rest of the line) are both handled, and a line that is
  nothing but a gloss is skipped rather than claiming the headword slot.
* **`resolver.py`** — decides what a note gets. The first line is the headword
  and is looked up whole first, because one recording of `не за что` beats
  three of `не`, `за` and `что`; only if the phrase is missing is it covered by
  the longest pieces that exist. Later lines are looked up whole and never
  split, so a textbook example sentence is left silent rather than stitched
  together out of seven different speakers.
* **Language-aware accent handling.** A combining acute on a Cyrillic letter is
  a stress mark and is removed (`ме́сто` → `место`); an accent on a Latin or
  Greek letter is spelling and is kept (`élève`, `está`). `ё` is preserved,
  since `её` has recordings and `ее` has none. Stress written as markup
  (`Н<u>е</u>когда`) or as a capital (`очкОв`) is handled too.
* **`coverHeadwordsUpToWords`** (6) — the longest headword still worth covering
  word by word. Past that it is a sentence wearing a headword's hat and is
  looked up whole or not at all.
* **A lookup cache** for the length of a deck run, so the CDN is asked about
  `не` once rather than once per card.
* **Tests.** `cd tests && python -m unittest discover` runs 65. The text
  handling and the lookup policy need nothing installed; the 14 dialog tests
  stub out Anki but need PyQt6, and skip without it.

### Changed

* **Config `Use sources besides Forvo` → `Use fallback sources`**, and it now
  defaults to `True`. The fallbacks (lingua libre, and openrussian for Russian)
  run only after the CDN comes up empty, and only for the headword, so a deck
  run cannot turn into a crawl.
* `download_Audio` reports whether the file arrived, so a failed download no
  longer leaves a `[sound:]` tag pointing at nothing.
* Auto-fetch only writes a note when something actually changed, so rerunning
  over a finished deck no longer dirties every note for the next sync.
* Window titles dropped the forvo branding: "ForvoTTS Generator (Beta)" is now
  "Add TTS to Deck", and "Forvo TTS for" is "Add TTS for".

### Fixed

* **The deck box filters as you type.** It matches anywhere in the name, not
  just the start, and ignores case, so `не ни` or `bernet` finds the deck
  without scrolling to it. Typing only filters — the deck is not switched, and
  Start stays off, until one is actually picked; leftover filter text is
  replaced by the real deck name when the box loses focus.
* **The deck dropdown had no scrollbar** and grew until it covered the screen.
  It was the only combobox in the dialog missing `combobox-popup: 0`, which is
  what makes Qt use a scrollable list instead of a native popup. It is also
  wider now, sizes its popup to the longest deck name and elides in the middle,
  so deeply nested names stay distinguishable.
* **Selecting a second deck raised `'bool' object is not callable`.**
  `self.pushButtonStart.setDisabled = False` assigned over the button's method
  instead of calling it, so every later selection tried to call a boolean.
* **`<br>` was deleted without a separator**, so a two-line field arrived at
  the CDN as `Не раз (= много раз)Мы не раз ходили в это кафе.` and matched
  nothing. Inline stress markup had the opposite problem: `<u>` was replaced
  with a space, turning `Н<u>е</u>когда` into `Н е когда`.
* Newlines inside stored HTML are treated as whitespace rather than line
  breaks, which is what they are. Pasted conjugation tables are full of them.
* The fallback sources are no longer called with a whole multi-word phrase
  after the per-word search has already failed, and a failing fallback no
  longer aborts the run.

### Measured

Against the live CDN, on 250 random notes from the Russian decks:

| | before | after |
| --- | --- | --- |
| notes that get audio | 249 | 250 |
| notes that get exactly one recording | 180 | 180 |
| notes that get six or more | 8 | 0 |
| most recordings on one note | 9 | 5 |

Coverage was never really the problem; what got attached was. On the deck that
prompted this — two-line cards carrying a headword and an example sentence —
the old pipeline put between 2 and 11 loose words on every card and the
headword itself on none, because `<br>` and `<u>` were mangled before the
lookup ever happened:

```
before  8: ['Не', 'раз', 'много', 'не', 'раз', 'ходили', 'в', 'это']
after   1: ['Не раз']

before 11: ['Ни', 'за', 'что', 'ни', 'за', 'что', 'не', 'придёт', 'к', 'тебе', 'на']
after   1: ['Ни за что']
```

The five-recording worst case is a card listing every past-tense form
(`Сесть`, `Сел`, `Села`, `Село`, `Сели`), which is what it should get.
