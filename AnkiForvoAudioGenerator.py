from aqt.qt import *
from aqt import mw
from .AnkiAudioTools import (
    AudioClearingOptions,
    configBool,
    download_Audio,
    getConfig,
    getDefiniteConfigPath,
)
from .ovrofCDN import automated_fallback_lookup, cdn_lookup
from .openrussian import openrussian_lookup
from .resolver import DEFAULT_COVER_MAX_TOKENS, CachedLookup, resolve
import re


class AnkiForvoAudioGenerator(QThread):
    finished = pyqtSignal()
    countChanged = pyqtSignal(int)

    def __init__(self, forvoAudioTargets, cards, audioClearOption, useOpenRussian=False):
        super().__init__()
        self.forvoAudioTargets = forvoAudioTargets
        self.cards = cards
        self.audioClearOption = audioClearOption
        config = getConfig()
        self.coverMaxTokens = intOption(config, "coverHeadwordsUpToWords", DEFAULT_COVER_MAX_TOKENS)
        self.fallback = automated_fallback_lookup if configBool("Use fallback sources") else None
        # One cache for the whole run: a deck full of Russian asks about 'не'
        # dozens of times and the CDN only needs to answer once.
        self.lookup = CachedLookup(cdn_lookup)
        # OpenRussian fills whatever the CDN missed, but only when asked for:
        # it synthesises audio for any Russian text, so it is opt-in per run.
        self.gapFiller = CachedLookup(openrussian_lookup) if useOpenRussian else None

    def run(self):
        count = 0
        while count < len(self.cards):
            if(self.isInterruptionRequested()):
                self.countChanged.emit(0)
                return
            card = mw.col.get_card(self.cards[count])
            if(self.cardContainsTargets(card)):
                note = card.note()
                if(self.addAudioToNote(note)):
                    mw.col.update_note(note)
            count += 1
            self.countChanged.emit(count)
        print(f"Auto fetch done: {self.lookup.calls} lookups, {self.lookup.hits} served from cache")
        self.finished.emit()

    def addAudioToNote(self, note):
        """Fill every target field of one note. True when the note changed."""
        changed = False
        for target in self.forvoAudioTargets:
            existingValue = note[target.targetFieldName]
            targetValue = existingValue
            if(self.audioClearOption != AudioClearingOptions.NO_CLEAR):
                targetValue = self.clearPreviousInput(targetValue, self.audioClearOption)

            resolution = resolve(
                note[target.fieldName],
                target.language,
                self.lookup,
                cover_max_tokens=self.coverMaxTokens,
                fallback=self.fallback,
                gap_filler=self.gapFiller,
            )

            for audio in resolution.audios:
                filename = audio.getBucketFilename()
                soundTag = "[sound:" + filename + "]"
                if(soundTag in targetValue):
                    continue
                if(download_Audio(audio.link, getDefiniteConfigPath(), filename)):
                    targetValue += soundTag

            # Only touch the note when something actually changed, so a rerun
            # over a finished deck does not dirty every note for the sync.
            if(targetValue != existingValue):
                note[target.targetFieldName] = targetValue
                changed = True
        return changed

    def cardContainsTargets(self, card):
        for target in self.forvoAudioTargets:
            if(target.fieldName not in card.note().keys()):
                return False
        return True

    def clearPreviousInput(self, text, audioClearingOption):
        if(audioClearingOption == AudioClearingOptions.NO_CLEAR):
            return text
        elif(audioClearingOption == AudioClearingOptions.FULL_CLEAR):
            return ""
        elif(audioClearingOption == AudioClearingOptions.AUDIO_CLEAR):
            # Regex to gather all [sound:*] values and replace with nothing.
            pattern = r'\[sound:[^\]]+\.\w+\]'
            text = re.sub(pattern, '', text)
        return text


def intOption(config, key, default):
    try:
        return max(1, int(config.get(key, default)))
    except (TypeError, ValueError):
        return default
