from aqt.qt import *
from PyQt5.Qt import *  # type: ignore
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from aqt import mw
from aqt.utils import showInfo
from .AnkiForvoAudioGenerator import AnkiForvoAudioGenerator
from .AnkiAudioTools import AnkiAudioTarget, AudioClearingOptions, AcquisitionType, AnkiAudioGlobals

# TODO: To anyone even remotely familiar with QT, this probably looks horrendous. Revamp encouraged. 

class AutoForvoTts(QDialog):
    languages = ['Abaza_abq', 'Abkhazian_ab', 'Adygean_ady', 'Afar_aa', 'Afrikaans_af', 'Aghul_agx', 'Akan_ak', 'Albanian_sq', 'Algerian Arabic_arq', 'Algonquin_alq',
             'Amharic_am', 'Ancient Greek_grc', 'Arabic_ar', 'Aragonese_an', 'Arapaho_arp', 'Arbëresh_aae', 'Armenian_hy', 'Aromanian_rup', 'Assamese_as', 'Assyrian Neo-Aramaic_aii',
             'Asturian_ast', 'Avaric_av', 'Aymara_ay', 'Azerbaijani_az', 'Bakhtiari_bqi', 'Balochi_bal', 'Bambara_bm', 'Bardi_bcj', 'Bashkir_ba', 'Basque_eu', 'Bavarian_bar', 'Belarusian_be',
             'Bemba_bem', 'Bench_bcq', 'Bengali_bn', 'Biblical Hebrew_hbo', 'Bihari_bh', 'Bislama_bi', 'Bosnian_bs', 'Bouyei_pcc', 'Breton_br', 'Bulgarian_bg', 
             'Burmese_my', 'Burushaski_bsk', 'Buryat_bxr', 'Campidanese_sro', 'Cantonese_yue', 'Cape Verdean Creole_kea', 'Catalan_ca', 'Cebuano_ceb', 'Central Atlas Tamazight_tzm', 
             'Central Bikol_bcl', 'Chamorro_ch', 'Changzhou_plig', 'Chechen_ce', 'Cherokee_chr', 'Chichewa_ny', 'Chuvash_cv', 'Coptic_cop', 'Cornish_kw', 'Corsican_co', 
             'Cree_cr', 'Crimean Tatar_crh', 'Croatian_hr', 'Czech_cs', 'Dagbani_dag', 'Danish_da', 'Dari_prs', 'Divehi_dv', 'Dusun_dtp', 'Dutch_nl', 'Dzongkha_dz', 'Edo_bin', 
             'Egyptian Arabic_arz', 'Emilian_egl', 'English_en', 'Erzya_myv', 'Esperanto_eo', 'Estonian_et', 'Etruscan_ett', 'Ewe_ee', 'Ewondo_ewo', 'Faroese_fo', 'Fiji Hindi_hif', 
             'Fijian_fj', 'Finnish_fi', 'Flemish_vls', 'Franco-Provençal_frp', 'French_fr', 'Frisian_fy', 'Friulan_fur', 'Fulah_ff', 'Fuzhou_fzho', 'Ga_gaa', 'Galician_gl', 'Gan Chinese_gan', 
             'Georgian_ka', 'German_de', 'Gilaki_glk', 'Greek_el', 'Guarani_gn', 'Gujarati_gu', 'Gulf Arabic_afb', 'Gusii_guz', 'Haitian Creole_ht', 'Hakka_hak', 'Hassaniyya_mey', 'Hausa_ha', 
             'Hawaiian_haw', 'Hebrew_he', 'Herero_hz', 'Hiligaynon_hil', 'Hindi_hi', 'Hmong_hmn', 'Hungarian_hu', 'Icelandic_is', 'Igbo_ig', 'Iloko_ilo', 'Indonesian_ind', 'Ingush_inh', 
             'Interlingua_ia', 'Inuktitut_iu', 'Irish_ga', 'Italian_it', 'Iwaidja_ibd', 'Jamaican Patois_jam', 'Japanese_ja', 'Javanese_jv', 'Jeju_jje', 'Jiaoliao Mandarin_jliu', 
             'Jin Chinese_cjy', 'Judeo-Spanish_lad', 'Kabardian_kbd', 'Kabyle_kab', 'Kalaallisut_kl', 'Kalenjin_kln', 'Kalmyk_xal', 'Kannada_kn', 'Karachay-Balkar_krc', 'Karakalpak_kaa', 
             'Kashmiri_ks', 'Kashubian_csb', 'Kazakh_kk', 'Khasi_kha', 'Khmer_km', 'Kikuyu_ki', 'Kimbundu_kmb', 'Kinyarwanda_rw', 'Kirundi_rn', 'Klingon_tlh', 'Komi_kv', 
             'Konkani_gom', 'Korean_ko', 'Kotava_avk', 'Krio_kri', 'Kurdish_ku', 'Kurmanji_kmr', 'Kutchi_kfr', 'Kyrgyz_ky', 'Ladin_lld', 'Lakota_lkt', 'Lao_lo', 'Latgalian_ltg', 
             'Latin_la', 'Latvian_lv', 'Laz_lzz', 'Lezgian_lez', 'Ligurian_lij', 'Limburgish_li', 'Lingala_ln', 'Lithuanian_lt', 'Lombard_lmo', 'Louisiana Creole_lou', 'Low German_nds', 
             'Lower Yangtze Mandarin_juai', 'Lozi_loz', 'Luganda_lg', 'Luo_luo', 'Lushootseed_lut', 'Luxembourgish_lb', 'Macedonian_mk', 'Mainfränkisch_vmf', 'Malagasy_mg', 'Malay_ms', 
             'Malayalam_ml', 'Maltese_mt', 'Manchu_mnc', 'Mandarin Chinese_zh', 'Mansi_mns', 'Manx_gv', 'Māori_mi', 'Mapudungun_arn', 'Marathi_mr', 'Mari_chm', 'Marshallese_mh', 
             'Masbateño_msb', 'Mauritian Creole_mfe', 'Mazandarani_mzn', 'Mbe_mfo', 'Mennonite Low German_pdt', 'Micmac_mic', 'Middle Chinese_ltc', 'Middle English_enm', 
             'Min Dong_cdo', 'Min Nan_nan', 'Minangkabau_min', 'Mingrelian_xmf', 'Minjaee Luri_lrc', 'Mohawk_moh', 'Moksha_mdf', 'Moldovan_mo', 'Mongolian_mn', 'Moroccan Arabic_ary', 
             'Nahuatl_nah', 'Naskapi_nsk', 'Navajo_nv', 'Naxi_nxq', 'Ndonga_ng', 'Neapolitan_nap', 'Nepal Bhasa_new', 'Nepali_ne', 'Nogai_nog', 'North Levantine Arabic_apc', 'Northern Sami_sme', 
             'Norwegian_no', 'Norwegian Nynorsk_nn', 'Nuosu_ii', 'Nǀuu_ngh', 'Occitan_oc', 'Ojibwa_oj', 'Okinawan_ryu', 'Old English_ang', 'Old Norse_non', 'Old Turkic_otk', 'Oriya_or', 
             'Oromo_om', 'Ossetian_os', 'Ottoman Turkish_ota', 'Palauan_pau', 'Palenquero_pln', 'Pali_pi', 'Pangasinan_pag', 'Papiamento_pap', 'Pashto_ps', 'Pennsylvania Dutch_pdc', 
             'Persian_fa', 'Picard_pcd', 'Piedmontese_pms', 'Pitjantjatjara_pjt', 'Polish_pl', 'Portuguese_pt', 'Pu-Xian Min_cpx', 'Pulaar_fuc', 'Punjabi_pa', 'Quechua_qu', 
             'Quenya_qya', 'Quiatoni Zapotec_zpf', 'Rapa Nui_rap', 'Reunionese Creole_rcf', 'Romagnol_rgn', 'Romani_rom', 'Romanian_ro', 'Romansh_rm', 'Rukiga_cgg', 
             'Russian_ru', 'Rusyn_rue', 'Samoan_sm', 'Sango_sg', 'Sanskrit_sa', 'Saraiki_skr', 'Sardinian_sc', 'Scots_sco', 'Scottish Gaelic_gd', 'Seediq_trv', 'Serbian_sr', 
             'Shanghainese_jusi', 'Shilha_shi', 'Shona_sn', 'Siberian Tatar_sty', 'Sicilian_scn', 'Silesian_szl', 'Silesian German_sli', 'Sindhi_sd', 'Sinhalese_si', 'Slovak_sk', 
             'Slovenian_sl', 'Somali_so', 'Soninke_snk', 'Sotho_st', 'Southwestern Mandarin_xghu', 'Spanish_es', 'Sranan Tongo_srn', 'Sundanese_su', 'Swabian German_swg', 'Swahili_sw', 
             'Swati_ss', 'Swedish_sv', 'Swiss German_gsw', 'Sylheti_syl', 'Tagalog_tl', 'Tahitian_ty', 'Tajik_tg', 'Talossan_tzl', 'Talysh_tly', 'Tamil_ta', 'Tatar_tt', 'Telugu_te', 
             'Thai_th', 'Tibetan_bo', 'Tigrinya_ti', 'Toisanese Cantonese_tisa', 'Tok Pisin_tpi', 'Toki Pona_x-tp', 'Tondano_tdn', 'Tongan_to', 'Tswana_tn', 'Tunisian Arabic_aeb', 
             'Turkish_tr', 'Turkmen_tk', 'Tuvan_tyv', 'Twi_tw', 'Ubykh_uby', 'Udmurt_udm', 'Ukrainian_uk', 'Upper Saxon_sxu', 'Upper Sorbian_hsb', 'Urdu_ur', 'Uyghur_ug', 'Uzbek_uz', 
             'Venda_ve', 'Venetian_vec', 'Vietnamese_vi', 'Volapük_vo', 'Võro_vro', 'Walloon_wa', 'Welsh_cy', 'Wenzhounese_qjio', 'Wolof_wo', 'Wu Chinese_wuu', 'Xhosa_xh', 'Xiang Chinese_hsn', 
             'Yakut_sah', 'Yeyi_yey', 'Yiddish_yi', 'Yoruba_yo', 'Yucatec Maya_yua', 'Yupik_esu', 'Zazaki_zza', 'Zhuang_za', 'Zulu_zu']
    #print(languages)
    def __init__(self, parent):
        super(AutoForvoTts, self).__init__(parent)
        self.setupUi(self)

    def addFieldOption(self, targetFieldName):
        #Hbox
        container = QHBoxLayout()
        #CheckBox
        checkbox = QCheckBox(self.scrollAreaWidgetContents)
        checkbox.setText(targetFieldName)
        # Language Select ComboBox
        languageSelectBox = QComboBox(self.scrollAreaWidgetContents)
        languageSelectBox.addItems(self.languages)
        languageSelectBox.setStyleSheet("combobox-popup: 0;")
        # Field Select ComboBox
        fieldSelectBox = QComboBox(self.scrollAreaWidgetContents)
        fieldSelectBox.setFocusPolicy(Qt.StrongFocus)
        fieldSelectBox.addItems(self.fieldNames)
        fieldSelectBox.setCurrentIndex(self.fieldNames.index(targetFieldName))
        fieldSelectBox.setStyleSheet("combobox-popup: 0;")
        # add them to the Hbox
        container.addWidget(checkbox)
        container.addWidget(languageSelectBox)
        container.addWidget(fieldSelectBox)        
        self.verticalLayout.addLayout(container)
        self.fieldList.append([checkbox, languageSelectBox, fieldSelectBox])

    def deckSeletionChanged(self, deckName):
        self.fieldList = [] # 2d array of object, 1d = 1 row, 2d = the row's widgets
        try:
            self.pushButtonStart.setDisabled = True
            self.deleteItemsOfLayout(self.verticalLayout)
            deck = mw.col.decks.byName(deckName)
            # get cards from deck. use double quotes in case of spaces
            self.cards = mw.col.find_cards("\"deck:" + str(deckName) + "\"")
            # take last card's fields (keys)
            card = mw.col.getCard(self.cards[-1])
            self.fieldNames = card.note().keys()
            for field in self.fieldNames:
                #add to the scroll area: Checkbox, languageComboBox, FieldComboBox
                self.addFieldOption(field)
            self.pushButtonStart.setDisabled = False
        except IndexError:
            showInfo("Error: Couldn't find cards for selected deck!")
        except Exception as e:
            showInfo("Unknow error: " + str(e))
        
        

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
        self.labelProgrssbarDialog.setAlignment(Qt.AlignCenter)
        
        # add languages self.comboBoxDeckSelection.addItem("")

        # deck label
        self.lblSelectDeck = QLabel(Dialog)
        self.lblSelectDeck.setGeometry(QRect(190, 10, 121, 16))
        self.lblSelectDeck.setObjectName("lblSelectDeck")
        #start button
        self.pushButtonStart = QPushButton(Dialog)
        self.pushButtonStart.setGeometry(QRect(195, 350, 90, 28))
        self.pushButtonStart.setObjectName("pushButtonStart")
        self.pushButtonStart.clicked.connect(self.startTheScraping)
        #
        self.lblSelectFields = QLabel(Dialog)
        self.lblSelectFields.setGeometry(QRect(100, 70, 261, 16))
        self.lblSelectFields.setObjectName("lblSelectFields")
        #optional checkbox clear previous input
        self.checkBoxClearPreviousInput = QCheckBox(Dialog)
        self.checkBoxClearPreviousInput.setGeometry(QRect(22, 250, 241, 21))
        self.checkBoxClearPreviousInput.setChecked(False)
        self.checkBoxClearPreviousInput.setObjectName("checkBoxClearPreviousInput")

        #additional Radio button options for clearing previous audio
        self.clearOptionsContainerWidget = QWidget(Dialog)
        self.clearOptionsContainerWidget.setGeometry(QRect(32, 270, 441, 34))
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
        
        self.lblScrapingOptions = QLabel(Dialog)
        self.lblScrapingOptions.setText("Acquisition method:")
        self.lblScrapingOptions.setGeometry(QRect(25, 300, 200, 31))
        #Radio buttons Hbox for the scraping methods
        self.ScrapingOptionsContainerWidget = QWidget(Dialog)
        self.ScrapingOptionsContainerWidget.setGeometry(QRect(32, 320, 441, 34))
        self.ScrapingOptionsContainerLayout = QHBoxLayout(self.ScrapingOptionsContainerWidget)
        self.ScrapingOptionsContainerLayout.setSpacing(6)
        # Radio button forvo and CDN option
        self.radiobtnForvoWithCDN = QRadioButton()
        self.radiobtnForvoWithCDN.setText("CDN + Forvo as Backup")
        # Radio button only forvo
        self.radiobtnForvo = QRadioButton()
        self.radiobtnForvo.setText("Only Forvo")
        self.radiobtnForvo.setChecked(True)
        self.ScrapingOptionsContainerLayout.addWidget(self.radiobtnForvoWithCDN)
        self.ScrapingOptionsContainerLayout.addWidget(self.radiobtnForvo)
        
        #scroll area
        self.scrollAreaFields = QScrollArea(Dialog)
        self.scrollAreaFields.setEnabled(True)
        self.scrollAreaFields.setGeometry(QRect(20, 120, 441, 121))
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scrollAreaFields.sizePolicy().hasHeightForWidth())
        self.scrollAreaFields.setSizePolicy(sizePolicy)
        self.scrollAreaFields.setFrameShape(QFrame.Box)
        self.scrollAreaFields.setFrameShadow(QFrame.Plain)
        self.scrollAreaFields.setLineWidth(2)
        self.scrollAreaFields.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scrollAreaFields.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scrollAreaFields.setWidgetResizable(True)
        self.scrollAreaFields.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
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
        self.comboBoxDeckSelection.setGeometry(QRect(140, 30, 82, 24))
        self.comboBoxDeckSelection.setMaximumWidth(200)
        self.comboBoxDeckSelection.setInsertPolicy(QComboBox.InsertAtBottom)
        self.comboBoxDeckSelection.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.comboBoxDeckSelection.setMinimumContentsLength(0)
        self.comboBoxDeckSelection.setObjectName("comboBoxDeckSelection")
        self.comboBoxDeckSelection.currentTextChanged.connect(self.deckSeletionChanged)

        self.comboBoxDeckSelection.addItems(mw.col.decks.allNames())
        self.comboBoxDeckSelection.view().setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        self.retranslateUi(Dialog)
        QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "ForvoTTS Generator (STILL IN TESTING)"))
        self.lblSelectDeck.setText(_translate("Dialog", "Select Deck:"))
        self.pushButtonStart.setText(_translate("Dialog", "Start"))
        self.lblSelectFields.setText(_translate("Dialog", "Select which field(s) and their language:"))
        self.checkBoxClearPreviousInput.setToolTip(_translate("Dialog", "Clear the audio field before adding the new tts to the audio field"))
        self.checkBoxClearPreviousInput.setText(_translate("Dialog", "Clear Previous Audio Field Input (?*)"))
        self.lblScrollField.setText(_translate("Dialog", "Field:"))
        self.lblScrollLanguage.setText(_translate("Dialog", "Language:"))
        self.lblTargetField.setText(_translate("Dialog", "Audio Field:"))

    def setListVBox(self):
        self.verticalLayout = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout.setSizeConstraint(QLayout.SetDefaultConstraint)
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
        sizePolicy = QSizePolicy(QSizePolicy.Ignored, QSizePolicy.Expanding)
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
        self.completed = 0
        #Determine which fields are to be used. field, language, and target field, maybe create a class?
        AnkiAudioTargets = []
        for row in self.fieldList:
            if(row[0].isChecked()):
                AnkiAudioTargets.append(AnkiAudioTarget(row[0].text(), row[1].currentText(), row[2].currentText()))

        #new thread to scrape audios with
        clearOption = AudioClearingOptions.NO_CLEAR
        if(self.checkBoxClearPreviousInput.isChecked()):
            if(self.radiobtnClearAllText.isChecked()):
                clearOption = AudioClearingOptions.FULL_CLEAR
            elif(self.radiobtnClearOnlySound.isChecked()):
                clearOption = AudioClearingOptions.AUDIO_CLEAR
        acquisitionType = AcquisitionType.CDN_WITH_FORVO
        if(self.radiobtnForvo.isChecked()):
            acquisitionType = AcquisitionType.ONLY_FORVO



        self.audioGenerator = AnkiForvoAudioGenerator(AnkiAudioTargets, self.cards, clearOption, acquisitionType)
        self.audioGenerator.countChanged.connect(self.onProgressChanged)
        self.audioGenerator.limit.connect(self.onForvoLimitReached)
        self.audioGenerator.finished.connect(self.finishTheScraping)
        self.audioGenerator.start()
        # Turn the start button into a cancel button

    def cancelTheScraping(self, event):
        #TODO: button text change does not happen because the parent method isn't done yet, either do this in another thread or see a QT background solution (Like Javafx's RunLater())
        self.pushButtonStart.setText("Cancelling...")
        self.pushButtonStart.setEnabled(False)
        while(self.audioGenerator.isRunning()):
            self.audioGenerator.requestInterruption()
        self.finishTheScraping()
        
    def finishTheScraping(self):
        AnkiAudioGlobals.forvoRequests = 0 
        self.progressBarAudio.setValue(0)
        self.labelProgrssbarDialog.setText("Done")
        self.pushButtonStart.clicked.disconnect(self.cancelTheScraping)
        self.pushButtonStart.setText("Start")
        self.pushButtonStart.clicked.connect(self.startTheScraping)
        self.changeMutableState(True)
        self.pushButtonStart.setEnabled(True)

    def onForvoLimitReached(self, value):
        self.finishTheScraping()
        self.labelProgrssbarDialog.setText("Maximum Forvo Downloads reached! "+"("+ str(value) + ")." + " Wait a bit before downloading again.")

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
        if(self.checkBoxClearPreviousInput.isChecked()):
            self.clearOptionsContainerWidget.setEnabled(state)
        self.ScrapingOptionsContainerWidget.setEnabled(state)
    def onProgressChanged(self, value):
        self.progressBarAudio.setValue(value)
        self.labelProgrssbarDialog.setText("Added Audio to card: " + str(value) + "/" + str(len(self.cards)))

    def setClearOptions(self, state):
        self.clearOptionsContainerWidget.setEnabled(state)
        if(state):    
            if(self.radiobtnClearAllText.isChecked() == False and self.radiobtnClearOnlySound.isChecked() == False):
                self.radiobtnClearOnlySound.setChecked(state)


