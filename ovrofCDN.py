import urllib.request
import urllib.parse
import json
from AnkiSimpleForvoAudio.AnkiAudioTools import AnkiAudioObject, AnkiAudioGlobals
from AnkiSimpleForvoAudio.bs4Scraper import lookup_word
from aqt import mw

'''
ovrofCDN is the Content Delivery Network I use to lighten the load on forvo.
I will first find the words on this CDN, if they exists, we can get their download paths.
If they don't, but they do in forvo, I'll send a request to have them added at a later date and the user will use forvo to get the audio. 
Current cdn is highly unreliable in terms of speed and availability. Lookup is done through a European hosted Heroku app with NoSQL.
Updating the cdn's audios has also become pretty tedious
'''
config = mw.addonManager.getConfig(__name__)

opener = urllib.request.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0')]
urllib.request.install_opener(opener)

def addWord(word, language):
    try:    
        wordEncoded = urllib.parse.quote(word)
        page=urllib.request.Request(AnkiAudioGlobals.DB_URL + "add/" + language + "/" + wordEncoded) 
        urllib.request.urlopen(page)
    except:
        pass

def find_word(word, language):
    # find all database rows for the exact word and return them. Also works for sentences.
    try:
        wordEncoded = urllib.parse.quote(word)
        page=urllib.request.Request(AnkiAudioGlobals.DB_URL + "lookup/" + language + "/" + wordEncoded) 
        body = urllib.request.urlopen(page).read()
        jsonlist = json.loads(body.decode("utf-8"))

        return json_to_AnkiAudioObjectList(jsonlist, language)
    except TimeoutError:
        raise TimeoutError("Timeout: cdn took too long to respond")
   
def find_word_with_highest_vote(word, language):
    try:
        wordEncoded = urllib.parse.quote(word)
        page=urllib.request.Request(AnkiAudioGlobals.DB_URL + "lookupOne/" + language + "/" + wordEncoded) 
        body = urllib.request.urlopen(page).read()
        jsonResult = json.loads(body.decode("utf-8"))
        return json_to_AnkiAudioObjectList(jsonResult, language)
    except:
        return []

def json_to_AnkiAudioObjectList(json, language):
    #print(json)
    audioObjects = []
    if(len(json) == 0):
        return audioObjects
    for word in json:
        wordId = word["path"].split("-")[-1].split(".")[0]
        downloadLink =  AnkiAudioGlobals.BUCKET_URL + language + "/" + word["word"] + "/" + word["path"]
        audioObjects.append(AnkiAudioObject(word["word"], wordId, downloadLink , str(word["votes"])))
    return audioObjects


def getWordsFromCdnWithForvoBackup(word, language, automatic):
    word = word.replace(" ", "_")
    return getWordFromCDN(word, language, automatic)

        
def getWordFromCDN(word, language, automatic=False):
    languageCode = language.split("_")[1]
    wordList = []
    print("CDN: Looking for " + word)
    if(automatic):
        wordList = find_word_with_highest_vote(word, language)
    else:
        wordList = find_word(word, language)
    if(len(wordList) == 0): #not found in CDN? look it up on forvo
        print("CDN: Not found on CDN. Using Forvo...")
        if(AnkiAudioGlobals.forvoRequests > config["MaxForvoDownloads"]):
            print("CDN: Max forvo request made during this session. You can edit this in 'config.json'. Do so at your own risk.")
        else:
            wordList = lookup_word(word, languageCode, automatic)
            AnkiAudioGlobals.forvoRequests += 1
            print("CDN: Total Forvo requests made: " + str(AnkiAudioGlobals.forvoRequests) + "/" + str(config["MaxForvoDownloads"]))
        if(len(wordList) > 0):
            print("CDN: Found " + word + " on Forvo. Added to CDN")
            addWord(word, language)
        else: # still not found? Look for the words seperately if it's a sentence
            if(word.__contains__("_")):
                wordList = getWordsFromCDN(word, language)
    return wordList


def getWordsFromCDN(words, language):
    wordList = []
    print("CDN: " + words + " not found. Looking up its seperate word...")
    for word in words.split("_"):
        sentenceWord = getWordFromCDN(word, language, True)
        if(len(sentenceWord) != 0): 
            wordList.append(sentenceWord[0])
    return wordList
