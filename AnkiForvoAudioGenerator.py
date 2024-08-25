from aqt.qt import *
import sys
import time
from aqt import mw
from .AnkiAudioTools import *
from .bs4Scraper import scrapeAnkiAudioObject, lookup_word
from .ovrofCDN import *
import random
import unicodedata
import requests
import re
import html


class AnkiForvoAudioGenerator(QThread):
    def __init__(self, forvoAudioTargets, cards, audioClearOption, acquisitionType):
        super().__init__()
        self.forvoAudioTargets = forvoAudioTargets
        self.cards = cards
        self.audioClearOption = audioClearOption
        self.acquisitionType = acquisitionType
        self.config = mw.addonManager.getConfig(__name__)
        self.ignorePunctuation = eval(self.config["ignorePunctuation"])

    finished = pyqtSignal()
    countChanged = pyqtSignal(int)
    limit = pyqtSignal(int)
    # Somehow, we need to do 1 lookup as a warm up, because the first lookup always get this error: unknown error (_ssl.c:3161)
    testresults = lookup_word("word", "English_en")

    def run(self):
        count = 0
        while count < len(self.cards):
            if(self.isInterruptionRequested()):
                self.countChanged.emit(0)
                return
            card = mw.col.get_card(self.cards[count])
            # Check if it has all the fields specified in the targets, if it does: loop. If it doesn't move on
            if(self.cardContainsTargets(card)): # pretty slow, maybe just do a try except
                # loop over the given targets
                for target in self.forvoAudioTargets: #target has: fieldName, targetFieldName and language (as code with getLanguageCode())
                    # fieldTarget is where the audio goes (previous audio cleared or not depends on the clearPreviousInput bool)
                    fieldNameValue = card.note()[target.fieldName]
                    card.note()[target.targetFieldName] = self.clearPreviousInput(card.note()[target.targetFieldName], self.audioClearOption)
                    # clear audio so the search won't include that part (separate from previous line)
                    fieldNameValue = self.clearPreviousInput(card.note()[target.targetFieldName], AudioClearingOptions.AUDIO_CLEAR)
                    fieldNameValue = self.remove_html_tags_and_entities(fieldNameValue)
                    # Acquisition type. Current options are: CDN With Forvo And Only Forvo
                    if(self.acquisitionType == AcquisitionType.CDN_WITH_FORVO):
                        words = getWordsFromCdnWithForvoBackup(fieldNameValue, target.language, True)
                    elif(self.acquisitionType == AcquisitionType.ONLY_FORVO):
                        words = scrapeAnkiAudioObject(fieldNameValue, target.getLanguageCode(), True)
                        AnkiAudioGlobals.forvoRequests +=1
                        if(AnkiAudioGlobals.forvoRequests > self.config["MaxForvoDownloads"]):
                            self.limit.emit(AnkiAudioGlobals.forvoRequests)
                            return
                    if(len(words) != 0):
                        # download the audio(s) from the given link.
                        for word in words:
                            #print("Downloading " + word.word + " to: " + word.getBucketFilename())
                            download_Audio(word.word, word.link , getDefiniteConfigPath(), word.getBucketFilename())
                            # set the audio to the target field as [sound:{name.ogg}] (if not already existing)
                            if(("[sound:" + word.getBucketFilename() + "]" in card.note()[target.targetFieldName] ) == False): #check duplicate
                                card.note()[target.targetFieldName] += "[sound:" + word.getBucketFilename() + "]"

                    mw.col.update_note(card.note())
            count +=1
            self.countChanged.emit(count)
        self.finished.emit()

    def cardContainsTargets(self, card): 
        for target in self.forvoAudioTargets:
            if((target.fieldName in card.note().keys()) == False):
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

    def remove_html_tags_and_entities(self, text):
        # Unescape HTML entities
        clean = html.unescape(text)
        # Remove HTML tags
        clean = re.sub(r'<.*?>', '', clean)
        return clean