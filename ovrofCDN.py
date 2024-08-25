from .bs4Scraper import forga_lookup, lookup_word

'''
ovrofCDN is the Content Delivery Network I use to lighten the load on forvo.
I will first find the words on this CDN, if they exists, we can get their download paths.
If they don't, but they do in forvo, I'll send a request to have them added at a later date and the user will use forvo to get the audio. 
Current cdn is highly unreliable in terms of speed and availability. Lookup is done through a European hosted Heroku app with NoSQL.
Updating the cdn's audios has also become pretty tedious
'''

def getWordsFromCdnWithForvoBackup(word, language, automatic):
    return getWordFromCDN(word, language, automatic)

        
def getWordFromCDN(word, language, automatic=False):
    wordList = []
    wordList.extend(forga_lookup(word, language, automatic))

    print("CDN: Looking for " + word)
    # if(automatic):
    #     wordList = find_word_with_highest_vote(word, language)
    # else:
    #     wordList = find_word(word, language)
    if(len(wordList) == 0): #not found in CDN? look it up on forvo
        print("CDN: Not found on CDN. Using Forvo...")
        wordList = lookup_word(word, language, automatic)
        
        if(len(wordList) == 0 and word.__contains__(" ")):
            wordList = getWordsFromCDN(word, language)

    return wordList


def getWordsFromCDN(words, language):
    wordList = []
    print("CDN: " + words + " not found. Looking up its seperate word...")
    for word in words.split(" "):
        sentenceWord = getWordFromCDN(word, language, True)
        if(len(sentenceWord) != 0): 
            wordList.append(sentenceWord[0])
    return wordList
