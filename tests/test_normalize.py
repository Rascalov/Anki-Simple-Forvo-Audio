# pyright: reportMissingImports=false
import unittest

import _bootstrap  # noqa: F401  (registers the add-on as an importable package)
from forvo_addon.normalize import (
    EXTRA,
    HEADWORD,
    clean,
    strip_bracketed,
    normalize,
    segment_field,
    strip_stress_marks,
    to_lines,
    tokenize,
)

RU = "Russian_ru"
FR = "French_fr"
EN = "English_en"


class TestStressMarks(unittest.TestCase):
    def test_cyrillic_acute_is_dropped(self):
        # The CDN has 'место' (8 recordings) and nothing at all for 'ме́сто'.
        self.assertEqual(strip_stress_marks("ме́сто"), "место")
        self.assertEqual(strip_stress_marks("За́мок"), "Замок")

    def test_yo_is_a_letter_not_an_accent(self):
        # 'её' has 7 recordings, 'ее' has none. Folding ё would lose the word.
        self.assertEqual(normalize("её", RU), "её")
        self.assertEqual(normalize("своём", RU), "своём")

    def test_short_i_survives(self):
        self.assertEqual(normalize("й", RU), "й")
        self.assertEqual(normalize("русский", RU), "русский")

    def test_latin_accents_are_orthography(self):
        # 'élève' has 3 recordings, 'eleve' has none.
        self.assertEqual(normalize("élève", FR), "élève")
        self.assertEqual(normalize("étudiant", FR), "étudiant")
        self.assertEqual(normalize("ça va", FR), "ça va")

    def test_decomposed_input_is_recomposed(self):
        self.assertEqual(normalize("élève", FR), "élève")

    def test_capital_inside_word_is_lowered(self):
        self.assertEqual(normalize("очкОв", RU), "очков")

    def test_leading_capital_is_kept(self):
        self.assertEqual(normalize("Москва", RU), "Москва")
        self.assertEqual(normalize("МГУ", RU), "МГУ")


class TestToLines(unittest.TestCase):
    def test_block_tags_break_lines(self):
        self.assertEqual(to_lines("один<br>два"), ["один", "два"])
        self.assertEqual(to_lines("<div>один</div><div>два</div>"), ["один", "два"])

    def test_inline_stress_markup_does_not_break_words(self):
        # Deleting <u> with a space gives 'Н е когда', which matches nothing.
        self.assertEqual(to_lines("Н<u>е</u>когда"), ["Некогда"])
        self.assertEqual(to_lines("Н<b>е</b> за что"), ["Не за что"])

    def test_sound_tags_are_dropped(self):
        self.assertEqual(to_lines("слово[sound:слово-1234.mp3]"), ["слово"])

    def test_entities_are_unescaped(self):
        self.assertEqual(to_lines("в океане&nbsp;"), ["в океане"])

    def test_source_newlines_are_whitespace_not_breaks(self):
        # Pasted tables wrap inside a cell. 'он\n\tприходит' is one form.
        self.assertEqual(to_lines("<div>он\n\tприходит</div>"), ["он приходит"])
        self.assertEqual(to_lines("<strong>Будущее\n\tвремя:</strong>"), ["Будущее время:"])


class TestStripBracketed(unittest.TestCase):
    def test_nested_brackets(self):
        self.assertEqual(clean("слово (betekenis (extra))"), "слово")

    def test_unclosed_bracket_swallows_the_rest(self):
        self.assertEqual(clean("слово (onafgesloten"), "слово")

    def test_square_and_curly_too(self):
        self.assertEqual(clean("слово [note] {aside}"), "слово")

    def test_a_stray_closer_is_not_treated_as_an_aside(self):
        self.assertEqual(strip_bracketed("слово) дом"), "слово) дом")


class TestClean(unittest.TestCase):
    def test_glosses_are_stripped(self):
        self.assertEqual(clean("Не раз (= много раз)"), "Не раз")
        self.assertEqual(clean("морковка (ontelbaar)"), "морковка")
        self.assertEqual(clean("разбираться в (+пред.)"), "разбираться в")

    def test_edge_punctuation_is_stripped(self):
        # 'Я не знаю' has 4 recordings, 'Я не знаю.' has none.
        self.assertEqual(clean("Я не знаю."), "Я не знаю")
        self.assertEqual(clean("— Спасибо."), "Спасибо")

    def test_inner_punctuation_is_kept(self):
        self.assertEqual(clean("Извини, я спешу"), "Извини, я спешу")
        self.assertEqual(clean("по-русски"), "по-русски")
        self.assertEqual(clean("c'est"), "c'est")


class TestSegmentField(unittest.TestCase):
    def test_headword_and_example_are_separate(self):
        segments = segment_field(
            "Не р<u>а</u>з (= много раз)<br>Мы не раз ходили в это кафе.", RU
        )
        self.assertEqual([s.text for s in segments], ["Не раз", "Мы не раз ходили в это кафе"])
        self.assertEqual([s.role for s in segments], [HEADWORD, EXTRA])

    def test_a_separator_inside_an_aside_does_not_split_the_line(self):
        # The gloss has to go before the line is cut, or 'мочь (kunnen' and
        # 'mogen' come out as two words to pronounce.
        segments = segment_field("мочь (kunnen / mogen)", RU)
        self.assertEqual([s.text for s in segments], ["мочь"])
        segments = segment_field("спрашивать (vragen - stellen)", RU)
        self.assertEqual([s.text for s in segments], ["спрашивать"])

    def test_asides_are_stripped_from_both_sides_of_a_pair(self):
        segments = segment_field("дом (huis) / квартира (flat)", RU)
        self.assertEqual([s.text for s in segments], ["дом", "квартира"])

    def test_a_line_that_is_only_an_aside_is_not_the_headword(self):
        segments = segment_field("(zelfstandig naamwoord)<br>дом", RU)
        self.assertEqual([s.text for s in segments], ["дом"])
        self.assertEqual(segments[0].role, HEADWORD)

    def test_aspect_pairs_split_into_headwords(self):
        segments = segment_field("решать – решить", RU)
        self.assertEqual([s.text for s in segments], ["решать", "решить"])
        self.assertTrue(all(s.role == HEADWORD for s in segments))

    def test_slash_splits_without_spaces(self):
        segments = segment_field("убивать/убить время", RU)
        self.assertEqual([s.text for s in segments], ["убивать", "убить время"])

    def test_in_word_hyphen_does_not_split(self):
        segments = segment_field("говорить по-русски", RU)
        self.assertEqual([s.text for s in segments], ["говорить по-русски"])

    def test_spaced_hyphen_splits(self):
        segments = segment_field("кот - коты", RU)
        self.assertEqual([s.text for s in segments], ["кот", "коты"])

    def test_later_lines_are_extras(self):
        segments = segment_field(
            "пенсионер (m)<div>пенсионерка (f)</div><div>пенсионеры (pl)</div>", RU
        )
        self.assertEqual([s.text for s in segments], ["пенсионер", "пенсионерка", "пенсионеры"])
        self.assertEqual([s.role for s in segments], [HEADWORD, EXTRA, EXTRA])

    def test_duplicates_are_dropped(self):
        segments = segment_field("Спасибо<br>спасибо", RU)
        self.assertEqual([s.text for s in segments], ["Спасибо"])

    def test_alternatives_are_not_split_on_later_lines(self):
        # 'он/она/оно зайдёт' is one conjugated form, not three pronouns.
        segments = segment_field("Зайти<br>он/она/оно зайдёт", RU)
        self.assertEqual([s.text for s in segments], ["Зайти", "он/она/оно зайдёт"])

    def test_label_lines_are_skipped(self):
        segments = segment_field("Сесть<br>Verleden tijd:<br>Сел", RU)
        self.assertEqual([s.text for s in segments], ["Сесть", "Сел"])

    def test_a_headword_line_ending_in_colon_is_kept(self):
        segments = segment_field("Зайти:<br>Будущее время:", RU)
        self.assertEqual([s.text for s in segments], ["Зайти"])

    def test_empty_field(self):
        self.assertEqual(segment_field("", RU), [])
        self.assertEqual(segment_field("<div><br></div>", RU), [])


class TestTokenize(unittest.TestCase):
    def test_edge_punctuation_is_stripped_from_tokens(self):
        # Regression: the comma made 'Девушка,' a token that could never match
        # the CDN's 'Девушка', so the gap filler produced a duplicate.
        self.assertEqual(tokenize("Девушка, читавшая книгу"), ["Девушка", "читавшая", "книгу"])

    def test_inner_punctuation_is_kept(self):
        self.assertEqual(tokenize("говорить по-русски"), ["говорить", "по-русски"])
        self.assertEqual(tokenize("c'est ça"), ["c'est", "ça"])

    def test_pure_punctuation_tokens_are_dropped(self):
        self.assertEqual(tokenize("Спасибо — всем"), ["Спасибо", "всем"])


if __name__ == "__main__":
    unittest.main()
