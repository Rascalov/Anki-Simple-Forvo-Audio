# pyright: reportMissingImports=false
import unittest

import _bootstrap  # noqa: F401  (registers the add-on as an importable package)
from forvo_addon.resolver import CachedLookup, resolve

RU = "Russian_ru"


class FakeAudio:
    def __init__(self, word, index=0):
        self.word = word
        self.id = f"{word}-{index}"
        self.link = f"https://cdn.example/{self.id}.mp3"

    def __repr__(self):
        return f"FakeAudio({self.id!r})"


class FakeCDN:
    """A CDN holding exactly the phrases it was given, matched like the real one."""

    def __init__(self, *phrases):
        self.phrases = {phrase.lower() for phrase in phrases}
        self.asked = []

    def __call__(self, value, language):
        self.asked.append(value)
        if value.lower() in self.phrases:
            return [FakeAudio(value, 0), FakeAudio(value, 1)]
        return []


def chosen(resolution):
    return resolution.chosen_for


class TestHeadword(unittest.TestCase):
    def test_multiword_headword_is_preferred_whole(self):
        cdn = FakeCDN("не за что", "не", "за", "что")
        result = resolve("Н<b>е</b> за что", RU, cdn)
        self.assertEqual(chosen(result), ["Не за что"])

    def test_headword_falls_back_to_longest_pieces(self):
        cdn = FakeCDN("местная", "газета")
        result = resolve("местная газета", RU, cdn)
        self.assertEqual(chosen(result), ["местная", "газета"])

    def test_cover_prefers_the_longest_piece_available(self):
        cdn = FakeCDN("работать", "в офисе", "в", "офисе")
        result = resolve("работать в офисе", RU, cdn)
        self.assertEqual(chosen(result), ["работать", "в офисе"])

    def test_uncoverable_word_is_skipped_not_faked(self):
        cdn = FakeCDN("странице")
        result = resolve("страница-на странице", RU, cdn)
        self.assertEqual(chosen(result), ["странице"])

    def test_long_headword_is_not_covered_word_by_word(self):
        # Seven words is a proverb, not a headword. Stitching it out of single
        # speakers is worse than silence, so nothing is taken.
        cdn = FakeCDN("Без труда", "не", "выловишь", "и", "рыбку", "из", "пруда")
        result = resolve("Без труда не выловишь и рыбку из пруда", RU, cdn)
        self.assertEqual(chosen(result), [])


class TestExtraLines(unittest.TestCase):
    def test_example_sentence_is_taken_only_if_it_exists_whole(self):
        cdn = FakeCDN("Некогда", "Спасибо")
        result = resolve("Н<u>е</u>когда<br>— Спасибо.", RU, cdn)
        self.assertEqual(chosen(result), ["Некогда", "Спасибо"])

    def test_example_sentence_is_never_covered_word_by_word(self):
        cdn = FakeCDN("Ничего", "Я", "не хочу", "делать")
        result = resolve("Ничег<u>о</u><br>Я ничего не хочу делать.", RU, cdn)
        self.assertEqual(chosen(result), ["Ничего"])

    def test_other_inflections_on_later_lines_are_taken(self):
        cdn = FakeCDN("пенсионер", "пенсионерка", "пенсионеры")
        result = resolve(
            "пенсионер (m)<div>пенсионерка (f)</div><div>пенсионеры (pl)</div>", RU, cdn
        )
        self.assertEqual(chosen(result), ["пенсионер", "пенсионерка", "пенсионеры"])


class TestWhatGetsTaken(unittest.TestCase):
    def test_every_line_the_cdn_has_is_taken(self):
        cdn = FakeCDN("a", "b", "c", "d")
        result = resolve("a<br>b<br>c<br>d", "English_en", cdn)
        self.assertEqual(chosen(result), ["a", "b", "c", "d"])

    def test_a_conjugation_table_takes_the_forms_that_exist(self):
        # The bare pronouns are on the CDN but the conjugated forms are not,
        # and an extra line is never split, so only the headword survives.
        cdn = FakeCDN("мочь", "я", "ты", "он", "мы", "вы", "они")
        field = "мочь<div>я мог<b>у</b></div><div>ты м<b>о</b>жешь</div><div>он м<b>о</b>жет</div>"
        result = resolve(field, RU, cdn)
        self.assertEqual(chosen(result), ["мочь"])

    def test_a_conjugation_table_whose_forms_exist_takes_them_all(self):
        cdn = FakeCDN("спать", "я сплю", "ты спишь", "он спит")
        field = "спать<div>я сплю</div><div>ты спишь</div><div>он спит</div>"
        result = resolve(field, RU, cdn)
        self.assertEqual(chosen(result), ["спать", "я сплю", "ты спишь", "он спит"])

    def test_a_lookup_is_only_made_once_per_note(self):
        cdn = FakeCDN("раз")
        resolve("раз<br>раз<br>раз", RU, cdn)
        self.assertEqual(cdn.asked, ["раз"])

    def test_same_recording_is_not_added_twice(self):
        cdn = FakeCDN("раз")
        result = resolve("раз / раз", RU, cdn)
        self.assertEqual(chosen(result), ["раз"])


class TestFallback(unittest.TestCase):
    def test_fallback_runs_only_when_the_cdn_found_nothing(self):
        cdn = FakeCDN()
        calls = []

        def fallback(value, language):
            calls.append(value)
            return [FakeAudio(value)]

        result = resolve("слово", RU, cdn, fallback=fallback)
        self.assertEqual(calls, ["слово"])
        self.assertEqual(chosen(result), ["слово"])

    def test_fallback_is_skipped_when_the_cdn_delivered(self):
        cdn = FakeCDN("слово")
        calls = []
        resolve("слово", RU, cdn, fallback=lambda v, l: calls.append(v) or [])
        self.assertEqual(calls, [])


class TestCachedLookup(unittest.TestCase):
    def test_repeated_questions_are_asked_once(self):
        cdn = FakeCDN("не")
        cached = CachedLookup(cdn)
        for _ in range(5):
            cached("не", RU)
        self.assertEqual(cdn.asked, ["не"])
        self.assertEqual((cached.calls, cached.hits), (1, 4))

    def test_a_failing_source_does_not_stop_the_run(self):
        def boom(value, language):
            raise RuntimeError("CDN is down")

        self.assertEqual(CachedLookup(boom)("не", RU), [])


if __name__ == "__main__":
    unittest.main()
