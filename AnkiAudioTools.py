import urllib.request
import urllib.parse
from enum import Enum
from bs4 import BeautifulSoup 
from aqt import mw
import random

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


class AnkiAudioObject:
    def __init__(self, word, id, link, votes=0):
        self.word = word
        self.id = id
        self.link = link
        self.votes = votes
    
    def getFilename(self): # used to be useful to access the vote amount
        return self.word + "-" + str(self.id) + "-" + self.votes + "." + self.link.split(".")[-1]
    def getBucketFilename(self): 
        #filename without the votes now used everywhere so a rename is needed. file extension now depends on config.
        fileExtension = (mw.addonManager.getConfig(__name__)["audioFileExtension"] or self.link.split(".")[-1])
        return self.word + "-" + str(self.id) + "." + fileExtension
    def getVotes(self):
        return int(self.votes.replace("votes", ""))

class AnkiAudioTarget:
    def __init__(self, fieldName, language, targetFieldName):
        self.fieldName = fieldName
        self.language = language
        self.targetFieldName = targetFieldName
    def getLanguageCode(self):
        return self.language.split('_')[1]

class AudioClearingOptions(Enum):
    FULL_CLEAR = 1
    AUDIO_CLEAR = 2
    NO_CLEAR = 3
    
class AcquisitionType(Enum):
    CDN_WITH_FORVO = 1
    ONLY_FORVO = 2

class AnkiAudioGlobals():
    BUCKET_URL = "https://languages.thegardengroup.nl/file/ovrofTest/"
    DB_URL = "https://cryptic-sierra-47984.herokuapp.com/" # yes, a free heroku app. money's tight.
    TEMP_FILE_PREFIX = "TEMP_AUDIO_FILE-"
    forvoRequests = 0

def download_Audio(word, link, path, filename, tempdownload = False):
    wordEncoded = urllib.parse.quote(word)
    link = link.replace(word, wordEncoded) # not applicable to forvo downloads. 
    if(tempdownload):
        filename = AnkiAudioGlobals.TEMP_FILE_PREFIX + filename
    try:
        urllib.request.urlretrieve(link, path + filename)
    except Exception as e:
        print("Failed to download " + filename)
        print(e)

