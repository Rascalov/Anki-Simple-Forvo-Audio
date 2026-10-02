# pyright: reportMissingImports=false
"""Deck selection in the auto-fetch dialog.

Needs PyQt6 but not Anki: aqt is stubbed out, and Qt runs on the offscreen
platform. Skipped when PyQt6 is not installed.
"""

import os
import sys
import types
import unittest

import _bootstrap  # noqa: F401  (registers the add-on as an importable package)

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QApplication, QComboBox
except ImportError:  # pragma: no cover
    raise unittest.SkipTest("PyQt6 is not installed")

DECKS = [
    "#Dailies",
    "#Dailies::Russian",
    "#Dailies::Russian::Tochka ru::урок 1.1",
    "#Dailies::Russian::Tochka Ru B1.2::урок 3.3::не ни",
    "CCNA",
    "CCNA::Day 32 Flashcards - IPv6 (Part 2)",
    "Git",
    "Kubernetes",
    "Empty Deck",
]
EMPTY = "Empty Deck"
NESTED = "#Dailies::Russian::Tochka Ru B1.2::урок 3.3::не ни"

MODALS = []


def stub_aqt():
    """Install just enough of aqt for the dialog to build."""
    if "aqt" in sys.modules:
        return

    class Note:
        def keys(self):
            return ["Front", "Back"]

    class Card:
        def note(self):
            return Note()

    class Collection:
        def __init__(self):
            self.decks = types.SimpleNamespace(
                all_names_and_ids=lambda: [
                    types.SimpleNamespace(name=name, id=i) for i, name in enumerate(DECKS)
                ]
            )

        def find_cards(self, query):
            return [] if EMPTY in query else [1, 2, 3]

        def get_card(self, cid):
            return Card()

    qt = types.ModuleType("aqt.qt")
    exec(
        "from PyQt6.QtWidgets import *\nfrom PyQt6.QtCore import *\nfrom PyQt6.QtGui import *",
        qt.__dict__,
    )
    utils = types.ModuleType("aqt.utils")
    utils.showInfo = lambda text, *a, **k: MODALS.append(text)
    sound = types.ModuleType("aqt.sound")
    sound.play = lambda *a, **k: None

    aqt = types.ModuleType("aqt")
    aqt.mw = types.SimpleNamespace(
        col=Collection(),
        addonManager=types.SimpleNamespace(
            getConfig=lambda name: {
                "downloadPath": "",
                "audioFileExtension": "mp3",
                "Use fallback sources": "True",
                "coverHeadwordsUpToWords": 6,
            },
            writeConfig=lambda *a, **k: None,
        ),
    )
    aqt.qt, aqt.utils, aqt.sound = qt, utils, sound
    sys.modules.update({"aqt": aqt, "aqt.qt": qt, "aqt.utils": utils, "aqt.sound": sound})


stub_aqt()
from forvo_addon.AutoForvoTts import AutoForvoTts  # noqa: E402

_app = QApplication.instance() or QApplication([])


class DeckBoxTest(unittest.TestCase):
    def setUp(self):
        MODALS.clear()
        self.dialog = AutoForvoTts(None)
        self.box = self.dialog.comboBoxDeckSelection
        self.completer = self.dialog.deckCompleter

    def tearDown(self):
        self.dialog.deleteLater()

    def type(self, text):
        """Type into the box the way a person does: text plus the edit signal."""
        self.box.lineEdit().setText(text)
        self.box.lineEdit().textEdited.emit(text)

    def completions(self, prefix):
        self.completer.setCompletionPrefix(prefix)
        model = self.completer.completionModel()
        return [model.index(row, 0).data() for row in range(model.rowCount())]


class TestOpening(DeckBoxTest):
    def test_first_deck_is_loaded_without_a_modal(self):
        self.assertEqual(self.dialog.loadedDeckName, DECKS[0])
        self.assertEqual(MODALS, [])
        self.assertTrue(self.dialog.pushButtonStart.isEnabled())
        self.assertEqual(len(self.dialog.fieldList), 2)

    def test_typing_cannot_invent_a_deck(self):
        self.assertTrue(self.box.isEditable())
        self.assertEqual(self.box.insertPolicy(), QComboBox.InsertPolicy.NoInsert)

    def test_enter_does_not_press_start(self):
        self.assertFalse(self.dialog.pushButtonStart.autoDefault())


class TestFiltering(DeckBoxTest):
    def test_matches_anywhere_in_the_name_ignoring_case(self):
        self.assertEqual(self.completer.filterMode(), Qt.MatchFlag.MatchContains)
        self.assertEqual(self.completer.caseSensitivity(), Qt.CaseSensitivity.CaseInsensitive)

    def test_lowercase_substring_finds_nested_decks(self):
        found = self.completions("tochka")
        self.assertEqual(len(found), 2)
        self.assertTrue(all("Tochka" in name for name in found))

    def test_matches_inside_a_word(self):
        self.assertIn("Kubernetes", self.completions("bernet"))

    def test_matches_the_tail_of_a_nested_name(self):
        self.assertIn(NESTED, self.completions("не ни"))

    def test_no_match_returns_nothing(self):
        self.assertEqual(self.completions("zzzzz"), [])


class TestCommitting(DeckBoxTest):
    def test_typing_filters_but_does_not_choose(self):
        self.type("tochka")
        self.assertEqual(self.dialog.loadedDeckName, DECKS[0])
        self.assertFalse(self.dialog.pushButtonStart.isEnabled())

    def test_picking_from_the_completer_loads_the_deck(self):
        count = self.box.count()
        self.type("не ни")
        self.completer.activated[str].emit(NESTED)
        self.assertEqual(self.dialog.loadedDeckName, NESTED)
        self.assertEqual(self.box.currentText(), NESTED)
        self.assertEqual(self.box.toolTip(), NESTED)
        self.assertTrue(self.dialog.pushButtonStart.isEnabled())
        self.assertEqual(self.box.count(), count, "filter text must not join the deck list")

    def test_picking_from_the_dropdown_loads_the_deck(self):
        index = DECKS.index("Git")
        self.box.setCurrentIndex(index)
        self.box.activated.emit(index)
        self.assertEqual(self.dialog.loadedDeckName, "Git")

    def test_a_fully_typed_name_commits_in_any_case(self):
        self.type("kubernetes")
        self.box.lineEdit().editingFinished.emit()
        self.assertEqual(self.dialog.loadedDeckName, "Kubernetes")
        self.assertEqual(self.box.currentText(), "Kubernetes")

    def test_leftover_filter_text_is_replaced_by_the_real_deck(self):
        index = DECKS.index("Git")
        self.box.setCurrentIndex(index)
        self.box.activated.emit(index)
        self.type("not a deck at all")
        self.box.lineEdit().editingFinished.emit()
        self.assertEqual(self.box.currentText(), "Git")
        self.assertEqual(self.dialog.loadedDeckName, "Git")
        self.assertTrue(self.dialog.pushButtonStart.isEnabled())


class TestEmptyDeck(DeckBoxTest):
    def select_empty(self):
        index = DECKS.index(EMPTY)
        self.box.setCurrentIndex(index)
        self.box.activated.emit(index)

    def test_it_reports_once_and_leaves_start_off(self):
        self.select_empty()
        self.assertEqual(len(MODALS), 1)
        self.assertIsNone(self.dialog.loadedDeckName)
        self.assertFalse(self.dialog.pushButtonStart.isEnabled())

    def test_losing_focus_afterwards_does_not_repeat_the_error(self):
        self.select_empty()
        for _ in range(5):
            self.box.lineEdit().editingFinished.emit()
        self.assertEqual(len(MODALS), 1)


if __name__ == "__main__":
    unittest.main()
