from aqt.qt import *
import aqt.sound
#from aqt.QtCore import QFile, QObject
from aqt import mw
from .AnkiAudioTools import languages, download_Audio, AnkiAudioGlobals, AnkiAudioObject
from .bs4Scraper import *
import os
import glob
from threading import *
import platform
import re


# TODO: To anyone even remotely familiar with QT, this probably looks horrendous. Revamp encouraged. 

class ForvoTts(QDialog):
    finalResult = None # to be a
    openrussian_session = ""
    def __init__(self, mw, targetNote, parent, focusedField, selectedText):
        QDialog.__init__(self, parent or mw)
        #super(ForvoTts, self).__init__(parent)
        self.textBox = QLineEdit(self)
        self.textBox.setGeometry(QRect(200, 50, 150, 30))
        self.textBox.setMinimumWidth(170)
        self.textBox.setPlaceholderText("Search...")
        self.config = mw.addonManager.getConfig(__name__)
        self.focusedField = focusedField
        self.textBox.setText(selectedText)
        self.targetNote = targetNote        
        self.setupUi(self)

    def setupUi(self, Dialog):
        Dialog.setObjectName("TTSDialog")
        Dialog.resize(320, 250) #w h 

        
        Dialog.setWindowTitle("Forvo TTS for")
        # finish button
        self.pushButtonStart = QPushButton(Dialog)
        self.pushButtonStart.setGeometry(QRect(195, 350, 150, 28))
        self.pushButtonStart.setObjectName("pushButtonStart")
        self.pushButtonStart.clicked.connect(self.start_lookup)
        self.pushButtonStart.setText("Search")
        # Lang selection
        self.languageSelectBox = QComboBox(Dialog)
        self.languageSelectBox.addItems(languages)
        self.languageSelectBox.setStyleSheet("combobox-popup: 0;")
        try:
            self.languageSelectBox.setCurrentIndex(self.languageSelectBox.findText(self.config["LastSelectedLanguage"]))
        except:
            pass

        # label destination field
        self.lblDestinationField = QLabel(Dialog)
        self.lblDestinationField.setGeometry(QRect(20, 45, 120, 30))
        self.lblDestinationField.setText("Destination Field:")
        # destination field combobox
        self.destinationFieldComboBox = QComboBox(Dialog)
        self.destinationFieldComboBox.setGeometry(QRect(140, 45, 150, 30))
        self.destinationFieldComboBox.addItems(self.targetNote.keys())

        try:
            if(self.config["LastSelectedField"] in self.targetNote.keys()):
                self.destinationFieldComboBox.setCurrentIndex(self.destinationFieldComboBox.findText(self.config["LastSelectedField"]))
            elif(isinstance(self.focusedField, int)):
                self.destinationFieldComboBox.setCurrentIndex(self.focusedField)
        except:
            if(isinstance(self.focusedField, int)):
                self.destinationFieldComboBox.setCurrentIndex(self.focusedField)
            
        if(eval(self.config["Remember language on a per deck basis"])):
            try:
                deck = mw.col.decks.get(self.targetNote.cards()[0].did)
            except:
                deck = mw.col.decks.current()
            # Get current deck's description
            description = deck["desc"]
            # Lazy lookup for string inside brackers
            pattern = r"\[(.*?)\]"
            matches = re.findall(pattern, description)  # Find all matches
            if matches:
                self.languageSelectBox.setCurrentIndex(self.languageSelectBox.findText(matches[0]))
        #vbox 
        #self.mainContainerLayout = QVBoxLayout(Dialog)
        #self.mainContainerLayout.setGeometry(QRect(0, 20, 320, 35))
        # search hbox

        self.searchHbox = QHBoxLayout(Dialog)
        self.searchHbox.setGeometry(QRect(0, 30, 320, 35))
        self.searchHbox.addWidget(self.textBox)
        self.searchHbox.addWidget(self.languageSelectBox)
        self.searchHbox.addWidget(self.pushButtonStart)
        self.searchHbox.setAlignment(Qt.AlignmentFlag.AlignTop)
        #self.mainContainerLayout.addLayout(self.searchHbox)

        #label scrollfield results
        self.lblScrollFieldResults = QLabel(Dialog)
        self.lblScrollFieldResults.setGeometry(QRect(20, 70, 110, 30))
        self.lblScrollFieldResults.setText("Results:")
        #scroll area
        self.scrollAreaFields = QScrollArea(Dialog)
        self.scrollAreaFields.setEnabled(True)
        self.scrollAreaFields.setGeometry(QRect(20, 100, 441, 121))
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scrollAreaFields.sizePolicy().hasHeightForWidth())
        self.scrollAreaFields.setSizePolicy(sizePolicy)
        self.scrollAreaFields.setFrameShape(QFrame.Shape.Box)
        self.scrollAreaFields.setFrameShadow(QFrame.Shadow.Plain)
        self.scrollAreaFields.setLineWidth(2)
        self.scrollAreaFields.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scrollAreaFields.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scrollAreaFields.setWidgetResizable(True)
        self.scrollAreaFields.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        self.scrollAreaFields.setObjectName("scrollAreaFields")
        self.createScrollAreaWidgetContents()
        self.setListVBox()

        self.scrollAreaFields.setWidget(self.scrollAreaWidgetContents)



    def setListVBox(self):
        self.verticalLayout = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.verticalLayout.setContentsMargins(0, 10, 0, 0)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setObjectName("verticalLayout")

    def createScrollAreaWidgetContents(self):
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 100, 300, 100))
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scrollAreaWidgetContents.sizePolicy().hasHeightForWidth())
        self.scrollAreaWidgetContents.setSizePolicy(sizePolicy)
        self.scrollAreaWidgetContents.setSizeIncrement(QSize(0, 0))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")

    def start_lookup(self, context):
        self.currentSearchResults = {}
        self.deleteItemsOfLayout(self.verticalLayout)
        results = []
        if(eval(self.config["Use sources besides Forvo"])):
            results.extend(lookup_word_lingua_libre(self.textBox.text(), self.languageSelectBox.currentText().split("_")[1]))

        results.extend(lookup_word(self.textBox.text(), self.languageSelectBox.currentText().split("_")[1]))
        if(len(results) == 0 and self.languageSelectBox.currentText() == "Russian_ru" and eval(self.config["Use sources besides Forvo"])):
            # Additional yandex translation. 
            results.extend(scrape_yandex_tts(self.textBox.text()))
            self.lblScrollFieldResults.setText("OpenRussian:")
        elif(len(results) == 0):
            self.lblScrollFieldResults.setText("No results found...")
        else:
            self.lblScrollFieldResults.setText("Results:")
        for result in results:
            print(result.getBucketFilename())
            self.currentSearchResults[result.getBucketFilename()] = result
            self.addResult(result) #add result to the scroll
            
    def addResult(self, ankiAudioObject):
        print("adding result")
        #Hbox
        container = QHBoxLayout()
        #Label with the name 
        label = QLabel(self.scrollAreaWidgetContents)
        label.setText(ankiAudioObject.getBucketFilename())
        # Preview button
        previewButton = QPushButton(self.scrollAreaWidgetContents)
        previewButton.setText("Preview Audio")
        previewButton.clicked.connect(lambda: self.previewAudio(ankiAudioObject))
        # Add button
        addButton = QPushButton(self.scrollAreaWidgetContents)
        addButton.setText("Choose and close")
        addButton.clicked.connect(lambda: self.insertIntoCard(ankiAudioObject))
        # add them to the Hbox
        container.addWidget(label)
        container.addWidget(previewButton)
        container.addWidget(addButton)        
        self.verticalLayout.addLayout(container)

    def previewAudio(self, audioObject):
        #download as temp, maybe do an exists check first?
        fullpath = self.getDefinteConfigPath() + AnkiAudioGlobals.TEMP_FILE_PREFIX + audioObject.getBucketFilename()
        if(os.path.isfile(fullpath)):
            print(fullpath + " is a file, playing...")
            aqt.sound.play(fullpath)
        else:
            print(fullpath + " is not a file,downaloding...")
            download_Audio(audioObject.word, audioObject.link, self.getDefinteConfigPath(), audioObject.getBucketFilename(), True)
            aqt.sound.play(fullpath)

    def insertIntoCard(self, ankiAudioObject):
        #select the forvo audio to add. 
        fullpath = self.getDefinteConfigPath() + AnkiAudioGlobals.TEMP_FILE_PREFIX + ankiAudioObject.getBucketFilename()
        if(os.path.isfile(fullpath)): # if it was a temp file, rename it
            print("Renaming temporary file ", ankiAudioObject.getBucketFilename() , "to permanent file")
            os.rename(fullpath, self.getDefinteConfigPath() + ankiAudioObject.getBucketFilename())
        else: # else download it without temp prefix
            print("Downloading ", ankiAudioObject.word, " to ", self.getDefinteConfigPath() + ankiAudioObject.getBucketFilename())
            download_Audio(ankiAudioObject.word, ankiAudioObject.link, self.getDefinteConfigPath(), ankiAudioObject.getBucketFilename())
        
        if(eval(self.config["Remember language on a per deck basis"])):
            # Get current deck's description and adjust it if language
            try:
                deck = mw.col.decks.get(self.targetNote.cards()[0].did)
            except:
                deck = mw.col.decks.current()
            description = deck["desc"]
            if(not description.startswith("[" + self.languageSelectBox.currentText() +"]")):
                deck["desc"]  = "[" + self.languageSelectBox.currentText() +"]" + deck["desc"]
                mw.col.decks.save(deck)                
        self.config["LastSelectedLanguage"] = self.languageSelectBox.currentText()
        self.config["LastSelectedField"] = self.destinationFieldComboBox.currentText()
        mw.addonManager.writeConfig(__name__, self.config)
        self.deleteTempFiles() #TODO: maybe in seperate thread
        self.finalResult = ankiAudioObject
        self.accept()

    def deleteItemsOfLayout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.setParent(None)
                else:
                    self.deleteItemsOfLayout(item.layout())

    def deleteTempFiles(self):
        for tempFile in glob.glob(self.getDefinteConfigPath() + AnkiAudioGlobals.TEMP_FILE_PREFIX + '*'):
            print("Deleting: ", tempFile)
            os.remove(tempFile)

    def getDefinteConfigPath(self):
        os_platform = platform.system()
        configPath = self.config["downloadPath"]
        if(configPath == ""):
            return mw.col.media.dir() + "\\" if os_platform == "Windows" else mw.col.media.dir() + "/"
        if(configPath[-1] != "\\" or configPath[-1] !="/"):
            configPath = configPath + "\\" if os_platform == "Windows" else configPath + "/"
        return configPath
