from aqt.qt import *
from aqt import mw
from aqt.utils import showInfo
from .AnkiForvoAudioGenerator import AnkiForvoAudioGenerator
from .AnkiAudioTools import AnkiAudioTarget, AudioClearingOptions, configBool, languages

# TODO: To anyone even remotely familiar with QT, this probably looks horrendous. Revamp encouraged.

# How many decks the dropdown shows before it starts scrolling, and how wide it
# is allowed to get for deeply nested deck names.
DECK_POPUP_ROWS = 15
DECK_POPUP_MAX_WIDTH = 900


class AutoForvoTts(QDialog):
    def __init__(self, parent):
        super(AutoForvoTts, self).__init__(parent)
        # The deck whose fields are currently loaded. Typing in the deck box
        # filters the list but chooses nothing, so this only moves when a deck
        # is actually picked.
        self.loadedDeckName = None
        self.attemptedDeckName = None
        self.selectingDeck = False
        self.deckNamesByLower = {}
        self.cards = []
        self.fieldList = []
        self.fieldNames = []
        self.setupUi(self)

    def addFieldOption(self, targetFieldName):
        #Hbox
        container = QHBoxLayout()
        #CheckBox
        checkbox = QCheckBox(self.scrollAreaWidgetContents)
        checkbox.setText(targetFieldName)
        # Language Select ComboBox
        languageSelectBox = QComboBox(self.scrollAreaWidgetContents)
        languageSelectBox.addItems(languages)
        languageSelectBox.setStyleSheet("combobox-popup: 0;")
        # Field Select ComboBox
        fieldSelectBox = QComboBox(self.scrollAreaWidgetContents)
        fieldSelectBox.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        fieldSelectBox.addItems(self.fieldNames)
        fieldSelectBox.setCurrentIndex(self.fieldNames.index(targetFieldName))
        fieldSelectBox.setStyleSheet("combobox-popup: 0;")
        # add them to the Hbox
        container.addWidget(checkbox)
        container.addWidget(languageSelectBox)
        container.addWidget(fieldSelectBox)        
        self.verticalLayout.addLayout(container)
        self.fieldList.append([checkbox, languageSelectBox, fieldSelectBox])

    def widenDeckPopup(self, names):
        """Let the dropdown be as wide as its longest deck name.

        The combobox has to fit the dialog, but the popup does not, and a
        nested name elided to '#Dailies::Russi...' is impossible to pick from.
        """
        view = self.comboBoxDeckSelection.view()
        metrics = view.fontMetrics()
        widest = max((metrics.horizontalAdvance(name) for name in names), default=0)
        scrollbar = view.verticalScrollBar().sizeHint().width()
        view.setMinimumWidth(min(widest + scrollbar + 24, DECK_POPUP_MAX_WIDTH))
        view.setTextElideMode(Qt.TextElideMode.ElideMiddle)

    def setupDeckCompleter(self):
        """Type-to-filter the deck list: matches anywhere in the name, any case.

        The completer runs over the combobox's own model, so picking from its
        popup moves the combobox with it.
        """
        completer = QCompleter(self.comboBoxDeckSelection.model(), self.comboBoxDeckSelection)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        completer.activated[str].connect(self.selectDeck)
        completer.popup().setMinimumWidth(self.comboBoxDeckSelection.view().minimumWidth())
        self.comboBoxDeckSelection.setCompleter(completer)
        self.deckCompleter = completer

    def onDeckActivated(self, index):
        """The user picked a row from the dropdown."""
        self.selectDeck(self.comboBoxDeckSelection.itemText(index))

    def onDeckTyped(self, text):
        """Typing filters the list. It is not a choice, so Start goes off."""
        if text != self.loadedDeckName:
            self.pushButtonStart.setEnabled(False)

    def onDeckTypingFinished(self):
        """Commit a fully typed deck name, or put the real one back."""
        typed = self.comboBoxDeckSelection.currentText().strip()
        if typed == self.attemptedDeckName:
            # Already tried this one; do not ask again every time focus moves.
            return
        match = self.deckNamesByLower.get(typed.lower())
        if match:
            self.selectDeck(match)
        elif self.loadedDeckName:
            # Half-typed filter text left in the box would look like a
            # selection that never happened.
            self.comboBoxDeckSelection.setEditText(self.loadedDeckName)
            self.pushButtonStart.setEnabled(True)

    def selectDeck(self, deckName, announce=True):
        """Load the fields of a deck the user has committed to.

        `announce` is off for the load that happens as the dialog opens, so an
        empty deck cannot greet you with a modal before you have done anything.
        """
        if self.selectingDeck or deckName == self.loadedDeckName:
            return
        # Opening a modal from here moves focus, which fires editingFinished
        # again; without this the error would reappear for as long as you click.
        self.selectingDeck = True
        try:
            self.loadDeck(deckName, announce)
        finally:
            self.selectingDeck = False

    def loadDeck(self, deckName, announce):
        self.loadedDeckName = None
        self.attemptedDeckName = deckName
        self.cards = []
        self.fieldList = [] # 2d array of object, 1d = 1 row, 2d = the row's widgets
        self.pushButtonStart.setEnabled(False)
        # The box is too narrow to show a nested name in full once it is picked.
        self.comboBoxDeckSelection.setToolTip(deckName)
        if self.comboBoxDeckSelection.currentText() != deckName:
            self.comboBoxDeckSelection.setEditText(deckName)
        self.deleteItemsOfLayout(self.verticalLayout)
        try:
            # get cards from deck. use double quotes in case of spaces
            self.cards = mw.col.find_cards("\"deck:" + str(deckName) + "\"")
            # take last card's fields (keys)
            card = mw.col.get_card(self.cards[-1])
            self.fieldNames = card.note().keys()
            for field in self.fieldNames:
                #add to the scroll area: Checkbox, languageComboBox, FieldComboBox
                self.addFieldOption(field)
            self.loadedDeckName = deckName
            self.pushButtonStart.setEnabled(True)
        except IndexError:
            if announce:
                showInfo("Error: Couldn't find cards for selected deck!")
        except Exception as e:
            if announce:
                showInfo("Unknown error: " + str(e))


    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(505, 450) #100 
        Dialog.setBaseSize(QSize(0, 0))
        Dialog.setToolTip("")
        #progressbar
        self.progressBarAudio = QProgressBar(Dialog)
        self.progressBarAudio.setEnabled(True)
        self.progressBarAudio.setGeometry(QRect(150, 390, 191, 23))
        self.progressBarAudio.setProperty("value", 0)
        self.progressBarAudio.setObjectName("progressBarAudio")       
        #progressbar label
        self.labelProgrssbarDialog = QLabel(Dialog)
        self.labelProgrssbarDialog.setGeometry(QRect(0, 420, 505, 20))
        self.labelProgrssbarDialog.setObjectName("labelProgrssbarDialog")
        self.labelProgrssbarDialog.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # add languages self.comboBoxDeckSelection.addItem("")

        # deck label
        self.lblSelectDeck = QLabel(Dialog)
        self.lblSelectDeck.setGeometry(QRect(190, 10, 121, 16))
        self.lblSelectDeck.setObjectName("lblSelectDeck")
        #start button
        self.pushButtonStart = QPushButton(Dialog)
        self.pushButtonStart.setGeometry(QRect(195, 350, 90, 28))
        self.pushButtonStart.setObjectName("pushButtonStart")
        # The deck box is a line edit now, and enter in a dialog fires the
        # default button. Starting a whole deck run by accident is not on.
        self.pushButtonStart.setAutoDefault(False)
        self.pushButtonStart.clicked.connect(self.startTheScraping)
        #
        self.lblSelectFields = QLabel(Dialog)
        self.lblSelectFields.setGeometry(QRect(100, 70, 261, 16))
        self.lblSelectFields.setObjectName("lblSelectFields")
        #optional checkbox: fill in audio the CDN could not find with openrussian
        self.checkBoxOpenRussian = QCheckBox(Dialog)
        self.checkBoxOpenRussian.setGeometry(QRect(22, 250, 300, 21))
        self.checkBoxOpenRussian.setChecked(configBool("Use openrussian for automated audio insertion"))
        self.checkBoxOpenRussian.setObjectName("checkBoxOpenRussian")

        #optional checkbox clear previous input
        self.checkBoxClearPreviousInput = QCheckBox(Dialog)
        self.checkBoxClearPreviousInput.setGeometry(QRect(22, 272, 241, 21))
        self.checkBoxClearPreviousInput.setChecked(False)
        self.checkBoxClearPreviousInput.setObjectName("checkBoxClearPreviousInput")

        #additional Radio button options for clearing previous audio
        self.clearOptionsContainerWidget = QWidget(Dialog)
        self.clearOptionsContainerWidget.setGeometry(QRect(32, 292, 441, 34))
        self.clearOptionsContainerLayout = QHBoxLayout(self.clearOptionsContainerWidget)
        self.clearOptionsContainerLayout.setSpacing(6)
        self.radiobtnClearAllText = QRadioButton()
        #self.radiobtnClearAllText.setGeometry(QRect(32, 270, 210, 21))
        self.radiobtnClearAllText.setText("Clear entire field (audio + text)")
        self.radiobtnClearOnlySound = QRadioButton()
        #self.radiobtnClearOnlySound.setGeometry(QRect(240, 270, 210, 21))
        self.radiobtnClearOnlySound.setText("Clear only audio")
        self.clearOptionsContainerWidget.setEnabled(False)
        self.checkBoxClearPreviousInput.stateChanged.connect(self.setClearOptions)
        self.clearOptionsContainerLayout.addWidget(self.radiobtnClearAllText)
        self.clearOptionsContainerLayout.addWidget(self.radiobtnClearOnlySound)

        #scroll area
        self.scrollAreaFields = QScrollArea(Dialog)
        self.scrollAreaFields.setEnabled(True)
        self.scrollAreaFields.setGeometry(QRect(20, 120, 441, 121))
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

        # Hbox that indicates the checkbox, field, language, and target field.
        self.horizontalLayoutWidget = QWidget(Dialog)
        self.horizontalLayoutWidget.setGeometry(QRect(20, 90, 441, 31))
        self.horizontalLayoutWidget.setObjectName("horizontalLayoutWidget")
        self.horizontalLayout = QHBoxLayout(self.horizontalLayoutWidget)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.checkBoxAllCheckBoxes = QCheckBox(self.horizontalLayoutWidget)
        self.checkBoxAllCheckBoxes.setObjectName("checkBoxAllCheckBoxes")
        self.checkBoxAllCheckBoxes.stateChanged.connect(self.checkAll)
        self.horizontalLayout.addWidget(self.checkBoxAllCheckBoxes)
        self.lblScrollField = QLabel(self.horizontalLayoutWidget)
        self.lblScrollField.setObjectName("lblScrollField")
        self.horizontalLayout.addWidget(self.lblScrollField)
        self.lblScrollLanguage = QLabel(self.horizontalLayoutWidget)
        self.lblScrollLanguage.setObjectName("lblScrollLanguage")
        self.horizontalLayout.addWidget(self.lblScrollLanguage)
        self.lblTargetField = QLabel(self.horizontalLayoutWidget)
        self.lblTargetField.setObjectName("lblTargetField")
        self.horizontalLayout.addWidget(self.lblTargetField)
        self.horizontalLayout.setStretch(1, 1)
        self.horizontalLayout.setStretch(2, 1)
        self.horizontalLayout.setStretch(3, 1)

        #deck combobox
        self.comboBoxDeckSelection = QComboBox(Dialog)
        self.comboBoxDeckSelection.setGeometry(QRect(140, 30, 225, 24))
        self.comboBoxDeckSelection.setObjectName("comboBoxDeckSelection")
        # A native popup ignores maxVisibleItems and grows until it covers the
        # screen, which a collection with many nested decks always does.
        # 'combobox-popup: 0' forces the scrollable list view instead.
        self.comboBoxDeckSelection.setStyleSheet("combobox-popup: 0;")
        self.comboBoxDeckSelection.setMaxVisibleItems(DECK_POPUP_ROWS)
        # Editable so the box can be typed into as a filter. NoInsert matters:
        # otherwise pressing enter on filter text adds it to the deck list.
        self.comboBoxDeckSelection.setEditable(True)
        self.comboBoxDeckSelection.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.comboBoxDeckSelection.lineEdit().setPlaceholderText("Type to filter decks...")
        decklist = mw.col.decks.all_names_and_ids()
        names = [deck.name for deck in decklist]
        self.deckNamesByLower = {name.lower(): name for name in names}
        self.comboBoxDeckSelection.addItems(names)
        self.comboBoxDeckSelection.view().setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        # The box itself is narrower than the dialog, but '#Dailies::Russian::
        # Tochka Ru B1.2::урок 3.3::не ни' still has to be readable while
        # choosing, so let the popup be as wide as its longest entry.
        self.widenDeckPopup(names)
        self.setupDeckCompleter()

        # Only a committed choice loads a deck. currentTextChanged would fire
        # on every keystroke, searching the collection for half a deck name.
        self.comboBoxDeckSelection.activated.connect(self.onDeckActivated)
        self.comboBoxDeckSelection.lineEdit().textEdited.connect(self.onDeckTyped)
        self.comboBoxDeckSelection.lineEdit().editingFinished.connect(self.onDeckTypingFinished)
        if names:
            self.selectDeck(names[0], announce=False)

        self.retranslateUi(Dialog)
        QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Add TTS to Deck"))
        self.lblSelectDeck.setText(_translate("Dialog", "Select Deck:"))
        self.pushButtonStart.setText(_translate("Dialog", "Start"))
        self.lblSelectFields.setText(_translate("Dialog", "Select which field(s) and their language:"))
        self.checkBoxClearPreviousInput.setToolTip(_translate("Dialog", "Clear the audio field before adding the new tts to the audio field"))
        self.checkBoxClearPreviousInput.setText(_translate("Dialog", "Clear Previous Audio Field Input (?*)"))
        self.checkBoxOpenRussian.setToolTip(_translate("Dialog", "When the CDN has no recording for a word or sentence, generate the missing audio with OpenRussian (Russian only)"))
        self.checkBoxOpenRussian.setText(_translate("Dialog", "Use OpenRussian for missing audio (Russian only)"))
        self.lblScrollField.setText(_translate("Dialog", "Field:"))
        self.lblScrollLanguage.setText(_translate("Dialog", "Language:"))
        self.lblTargetField.setText(_translate("Dialog", "Audio Field:"))

    def setListVBox(self):
        self.verticalLayout = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.verticalLayout.setContentsMargins(0, 10, 0, 0)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setObjectName("verticalLayout")

    def deleteItemsOfLayout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.setParent(None)
                else:
                    self.deleteItemsOfLayout(item.layout())

    def createScrollAreaWidgetContents(self):
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 328, 121))
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scrollAreaWidgetContents.sizePolicy().hasHeightForWidth())
        self.scrollAreaWidgetContents.setSizePolicy(sizePolicy)
        self.scrollAreaWidgetContents.setSizeIncrement(QSize(0, 0))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        
    def startTheScraping(self, event): #event is bool
        self.labelProgrssbarDialog.setText("Scraping...")
        self.pushButtonStart.clicked.disconnect(self.startTheScraping)
        self.pushButtonStart.setText("Cancel")
        self.pushButtonStart.clicked.connect(self.cancelTheScraping)
        self.changeMutableState(False)
        self.progressBarAudio.setMaximum(len(self.cards))
        #Determine which fields are to be used. field, language, and target field
        AnkiAudioTargets = []
        for row in self.fieldList:
            if(row[0].isChecked()):
                AnkiAudioTargets.append(AnkiAudioTarget(row[0].text(), row[1].currentText(), row[2].currentText()))

        clearOption = AudioClearingOptions.NO_CLEAR
        if(self.checkBoxClearPreviousInput.isChecked()):
            if(self.radiobtnClearAllText.isChecked()):
                clearOption = AudioClearingOptions.FULL_CLEAR
            elif(self.radiobtnClearOnlySound.isChecked()):
                clearOption = AudioClearingOptions.AUDIO_CLEAR

        #new thread to scrape audios with
        self.audioGenerator = AnkiForvoAudioGenerator(AnkiAudioTargets, self.cards, clearOption, self.checkBoxOpenRussian.isChecked())
        self.audioGenerator.countChanged.connect(self.onProgressChanged)
        self.audioGenerator.finished.connect(self.finishTheScraping)
        self.audioGenerator.start()

    def cancelTheScraping(self, event):
        self.pushButtonStart.setText("Cancelling...")
        self.pushButtonStart.setEnabled(False)
        while(self.audioGenerator.isRunning()):
            self.audioGenerator.requestInterruption()
        self.finishTheScraping()
        
    def finishTheScraping(self):
        self.progressBarAudio.setValue(0)
        self.labelProgrssbarDialog.setText("Done")
        self.pushButtonStart.clicked.disconnect(self.cancelTheScraping)
        self.pushButtonStart.setText("Start")
        self.pushButtonStart.clicked.connect(self.startTheScraping)
        self.changeMutableState(True)
        self.pushButtonStart.setEnabled(True)

    def checkAll(self, state):
        # No need to eval whether the state is checked or unchecked
        for row in self.fieldList:
            row[0].setCheckState(state) # just set all checkmark states equal to the given state:

    def changeMutableState(self, state):
        #enable or disable all the widgets that are used to start the scraping
        self.comboBoxDeckSelection.setEnabled(state)
        self.scrollAreaFields.setEnabled(state)
        self.checkBoxAllCheckBoxes.setEnabled(state)
        self.checkBoxClearPreviousInput.setEnabled(state)
        self.checkBoxOpenRussian.setEnabled(state)
        if(self.checkBoxClearPreviousInput.isChecked()):
            self.clearOptionsContainerWidget.setEnabled(state)

    def onProgressChanged(self, value):
        self.progressBarAudio.setValue(value)
        self.labelProgrssbarDialog.setText("Added Audio to card: " + str(value) + "/" + str(len(self.cards)))

    def setClearOptions(self, state):
        self.clearOptionsContainerWidget.setEnabled(state)
        if(state):    
            if(self.radiobtnClearAllText.isChecked() == False and self.radiobtnClearOnlySound.isChecked() == False):
                self.radiobtnClearOnlySound.setChecked(state)


