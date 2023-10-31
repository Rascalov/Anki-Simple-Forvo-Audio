from aqt.qt import *
import sys
import time
from aqt import mw
from .AnkiAudioTools import *
from .bs4Scraper import scrapeAnkiAudioObject
from .ovrofCDN import *
import random
import unicodedata

class AnkiForvoAudioGenerator(QThread):
    def __init__(self, forvoAudioTargets, cards, audioClearOption, acquisitionType):
        super().__init__()
        self.forvoAudioTargets = forvoAudioTargets
        self.cards = cards
        self.audioClearOption = audioClearOption
        self.acquisitionType = acquisitionType
        self.config = mw.addonManager.getConfig(__name__)
        self.ignorePunctuation = eval(self.config["ignorePunctuation"])
        # not so fast
        self.sleepTime = 0.75 
        print("Sleep time modifier per download: " + str(self.sleepTime) + " second(s).")

    finished = pyqtSignal()
    countChanged = pyqtSignal(int)
    limit = pyqtSignal(int)
    def run(self):
        count = 0

        while count < len(self.cards):
            if(self.isInterruptionRequested()):
                self.countChanged.emit(0)
                return
            card = mw.col.get_card(self.cards[count])
            # Check if it has all the fields specified in the targets, if it does: loop. If it doesn't move on
            if(self.cardContainsTargets(card)): # pretty slow, maybe just do a try except
                #print("card nr." + str(count) + " contains the targets" )
                # loop over the given targets
                for target in self.forvoAudioTargets: #target has: fieldName, targetFieldName and language (as code with getLanguageCode())
                    # fieldTarget is where the audio goes (previous audio cleared or not depends on the clearPreviousInput bool)
                    fieldNameValue = card.note()[target.fieldName]    
                    # If there is a sound with the fieldValue in it, skip it. 
                    if("[sound:" + fieldNameValue.replace(" ", "_") in card.note()[target.targetFieldName]): #kinda flawed, only works on the first word/sentence
                        continue              
                    card.note()[target.targetFieldName] = self.clearPreviousInput(card.note()[target.targetFieldName], self.audioClearOption)
                    if(self.ignorePunctuation):
                        tbl = dict.fromkeys(i for i in range(sys.maxunicode)
                                    if unicodedata.category(chr(i)).startswith('P'))
                        fieldNameValue = fieldNameValue.translate(tbl)
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
                            print("Downloading " + word.word + " to: " + word.getBucketFilename())
                            download_Audio(word.word, word.link , self.config["downloadPath"], word.getBucketFilename())
                            # set the audio to the target field as [sound:{name.ogg}] (if not already existing)
                            if(("[sound:" + word.getBucketFilename() + "]" in card.note()[target.targetFieldName] ) == False): #check duplicate (NOT replaced with line 38)
                                card.note()[target.targetFieldName] += "[sound:" + word.getBucketFilename() + "]"
                            time.sleep(self.sleepTime)
                            #time.sleep(random.randint(self.sleepTime, (self.sleepTime + 1)))
                    card.note().flush()
            count +=1
            self.countChanged.emit(count)
        self.finished.emit()

    def cardContainsTargets(self, card): 
        #print(card.note().keys())
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
            #imagine [sound: something.w/e]
            #ideally: gather all bracket pairs, if contains "sound:" then remove. 
            # [irrelevant] sometext [sound:textAudio.ogg]moretext[sound:textAudio.ogg][irrelevant]
            brackets = text.split('[')
            # would give { irrelevant] sometext , sound:textAudio.ogg]moretext ,  sound:textAudio.ogg] , irrelevant] }
            # Which can be split again per split
            for bracket in brackets:
                bracketText = bracket.split(']')[0]
                if(bracketText.__contains__("sound:")):
                    text = text.replace("[" + bracketText + "]", "")
        return text



