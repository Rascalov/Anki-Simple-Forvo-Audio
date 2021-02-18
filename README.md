# Installation
Either clone this repository to your Anki-Addons folder or download the zip in [Releases](https://github.com/Rascalov/Anki-Simple-Forvo-Audio/releases), unzip it, and put in your addon folder

You should be good to go. But should the audio not play, you might need to set the download path:

* Go to Anki>Tools>Add-ons <br>
* Select the addon
* Click on **Config**
* set your `downloadPath` to the path anki uses to save media 

On linux, mine looked like: <br>
`/home/user/.local/share/Anki2/User 1/collection.media/`

I read that on windows it looks like: <br> `C:\Users\Administrator\AppData\Roaming\Anki2\yourankiaccountname\collection.media`

result:

<img src="githubAssets/config.png" width =300 height=100>


# Anki Simple Forvo Audio
Main goal of this addon is to make forvo audio easy to apply to your anki cards (and doing so for **free** ).<br>
No forvo account is needed.

AwesomeTTS supports forvo, but only if you pay for an API key or subscribe to their patreon. <br> I wrote this to avoid monthly payments.

The addon has 2 functionalities:

## Select and fetch
Gif should make it straightforward. Select your word, rightclick on * Add Forvo Audio*. <br>
This brings you to a pop up where you can quickly search for your word, choose your language, and the destination field.
![Fetch Gif SHould be here](/githubAssets/Select-and-Fetch.gif)
You can also also preview the audios before you choose one.  

<br><br><br><br><br><br><br><br><br><br><br><br><br><br>

## Auto Fetch (NOT RECOMMENDED (yet))
My deformed son. <br>
It takes in a deck and, depending on the fields you select, downloads audios from either forvo or my own CDN that uses forvo when needed.<br>


It can save you some time and effort on large decks, **BUT** <br>
**Warning**: **Can get you ip banned if you overuse it!**

Forvo is cracking down on IP's that download too many audios from her site in bulks. I set a limit of 100 audios. 
You can edit this limit in the config, if you feel lucky. 

Use this feature at your own risk, I might find a safer way get the audios in bulks later on that's still free. 

![Generator Gif SHould be here](/githubAssets/AutoGenerator.gif)
