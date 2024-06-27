from bs4 import BeautifulSoup
import base64
import urllib.request
import urllib.parse
from .AnkiAudioTools import AnkiAudioObject, AnkiAudioGlobals
import string
import unicodedata
import sys
import traceback
import random
import re
import requests

"""
This scraper is used when my own cdn does not have the word(s) we seek.

This is my first experience with Python and scraping on it. Overal pretty positive experience.

I spent multiple days trying to get lxml working for linux windows and mac in the anki addon. 
But compiling it and using it in the anki addon folder proved too hard for my brain. My patience ran out.

I looked at other addons and their use of lxml, but none of their implementations worked on mine (then again, neither did their addons).
So I dropped lxml and used some bs4 which seems to work fine with maybe some speed loss on things like cssselect.

"""


#all the languages forvo supports with their language code used in forvo word pages
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

opener = urllib.request.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:77.0) Gecko/20100101 Firefox/77.0')]
urllib.request.install_opener(opener)

def get_forvo_page(url):
    try:
        # TODO: deeper exception handling
        page=urllib.request.Request(url) 
        infile=urllib.request.urlopen(page).read()
        data = infile.decode('UTF-8')
        soup = BeautifulSoup(data, "html.parser")
        return soup
    except Exception as e:
        print(str(e))
        return None

def getLanguages(listPage):
    #TODO: see line 99
    # takes a forvo language list page and returns all the languages with their code (I think forvo uses ISO 639-2)
    langList = []
    languagesUl = listPage.select_one("ul.alphabetically")
    for languageLi in languagesUl.findChildren("li", recursive=False): #LOL recursive lookup is true by default. Guess it makes sense, but got me confused (lxml habits die hard)
        languageName = languageLi.select_one("a").getText()
        languageCode = languageLi.select_one("abbr").getText()
        langList.append(languageName + "_" + languageCode)
    return langList


def updateForvoLanguages():
    # probably never needed, but useful if forvo adds extra languages
    languageList = []
    # You can't get all pagination numbers displayed on 1 page, I check page 1 and go up untill the page returns None (404)
    pageNumber = 1
    while(True): #TODO: Forvo has a single page with all languages and lang-codes. Use that instead of this
        page = get_forvo_page("https://forvo.com/languages/alphabetically/" + "page-" + str(pageNumber))
        if(page == None):
            break
        print("fetching languages from page: " + str(pageNumber))
        languageList.extend(getLanguages(page))
        pageNumber += 1
    print(languageList)
    return languageList


def get_audio_link(onclickFunction):
    #example js play functions from forvo:
    #Play(6166435,'OTg4MTIyMC8xMzgvOTg4MTIyMF8xMzhfMzM5MDIxLm1wMw==','OTg4MTIyMC8xMzgvOTg4MTIyMF8xMzhfMzM5MDIxLm9nZw==',false,'by80L280Xzk4ODEyMjBfMTM4XzMzOTAyMS5tcDM=','by80L280Xzk4ODEyMjBfMTM4XzMzOTAyMS5vZ2c=','h');return false;
    #Play(6687207,'OTU5NzcxMy8xMzgvOTU5NzcxM18xMzhfNjk2MDEyMi5tcDM=','OTU5NzcxMy8xMzgvOTU5NzcxM18xMzhfNjk2MDEyMi5vZ2c=',false,'','','l');return false;
    # All audios have an ogg version as a fallback on the mp3. Ogg is open source and compresses audio to a smaller size than mp3.
    # So I grab the ogg base64 string and decode it.
    base64audio = onclickFunction.split(',')[2].replace('\'', "")
    decodedLink = base64.b64decode(base64audio.encode('ascii')).decode('ascii')
    return "https://audio00.forvo.com/ogg/" + decodedLink

def get_forvo_audio_object(audioTag, word):
    audioid = audioTag["id"].split("_")[-1]
    audioLink =  get_audio_link(audioTag["onclick"])
    return AnkiAudioObject(word, audioid, audioLink)


def lookup_words(words, languageCode):
    #for each word add word to the list
    wordList = []
    for word in words:
        sentenceWord = lookup_word(word, languageCode, True) # add the first result
        if(sentenceWord != None and len(sentenceWord) != 0):
            wordList.append(sentenceWord[0])
    return wordList


def lookup_word(word, languageCode, automatic=False):
    audioList = []
    print("FORVO: Looking for " + word)
    wordEncoded = urllib.parse.quote(word)
    forvoPage = get_forvo_page("https://forvo.com/word/" + wordEncoded)
    if(forvoPage == None ):
        print("FORVO: Word not found (Page does not exist!)")
        return audioList # word not found

    speachSection = forvoPage.select_one("div#language-container-" + languageCode)
    if not speachSection:
        print("FORVO: Word not found (Language Container does not exist!)")
        return audioList # no results for that language-code
    
    pronounciations = speachSection.select(f"ul#phrase-pronunciations-list-{languageCode}-" )
    for pronounciation in pronounciations:
        pronounciation.decompose()

    div_audios = speachSection.select("div[id^='play_']")
    if(automatic):
        audioList.append(get_forvo_audio_object(div_audios[0], word))    
    else:
        for div_audio in div_audios:
            audioList.append(get_forvo_audio_object(div_audio, word))

    if len(audioList) == 0:
        print("No words found in existing countainer")
    return audioList


def lookup_word_lingua_libre(word, languageCode):
    audioList = []
    wordEncoded = urllib.parse.quote(word)
    page = get_forvo_page("https://lingualibre.org/index.php?search=" + wordEncoded)
    links = page.select("a[href^='/wiki/Q']")
    pattern = word +" | audio record - " + languageCode
    for link in links:
        clean_title = link["title"].replace("\u200E", "").lower()
        if clean_title.startswith(pattern):
            try:
                linkPage = get_forvo_page("https://lingualibre.org" + link['href'])
                wordID = link['href'][link['href'].find("Q"):]
                audioList.append(AnkiAudioObject(word, wordID , linkPage.select_one("source[type^='audio/ogg']")['src']))
            except Exception as e:
                print(str(e))
    return audioList

def scrapeAnkiAudioObject(word, languageCode, automatic=False):
    word = word.replace(' ', '_')
    wordlist = lookup_word(word, languageCode, automatic)
    if(len(wordlist) == 0 and word.__contains__("_")):
        #fallback: each word's audio will be looked for and used as multiple ogg's in anki. 
        # what if one of the words is not found? fuck it, ignored. 
        print("FORVO: Sentence not found, creating it with seperate words...")
        return lookup_words(word.split('_'), languageCode)
    AnkiAudioGlobals.forvoRequests += 1
    return wordlist

def scrape_yandex_tts(word):
    # Russian only (from en.openrussian.org)
    audioList = []
    url = f"https://api.openrussian.org/read/ru/{word}"
    response = requests.get(url, allow_redirects=False)
    headers = response.headers
    print(response.status_code)
    for header, value in response.headers.items():
        print(f"{header}: {value}")
    location = response.headers.get("Location")
    print(location)
    wordID = location.split('/')[-1].split('.mp3')[0]
    audioList.append(AnkiAudioObject(word, wordID , location))
    return audioList



# To debug, Comment out the AnkiAudioObject imports and make the audiolist append the element, not the object. (line 160-161) 
#print(lookup_word("слова", "ru"))

#print(lookup_word_lingua_libre("пять", "ru"))
