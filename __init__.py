from aqt import mw
from aqt.qt import *
from .AutoForvoTts import AutoForvoTts
from .ForvoTts import ForvoTts
from aqt import gui_hooks


def openForvoAudioGenerator():
    cardCount = mw.col.cardCount()
    config = mw.addonManager.getConfig(__name__)
    mw.myWidget = widget = AutoForvoTts(mw)
    widget.show()

action = QAction("Add Forvo TTS to deck", mw)
action.triggered.connect(openForvoAudioGenerator)
#mw.form.menuTools.addAction(action)

def addForvoTtsOption(editerWindow, qmenu):
    qmenu.addAction("Add Forvo Audio", lambda: forvoTts(editerWindow))


def forvoTts(editorWindow):
    editor = editorWindow.editor
    results = []
    note = editor.note
    widget = ForvoTts(mw, note, editor.parentWindow, editor.currentField, editorWindow.selectedText())
    if(widget.exec_()):
        result = widget.finalResult
        editor.web.setFocus()
        editor.web.eval("focusField(%d);" % int(widget.destinationFieldComboBox.currentIndex())) 
        editor.web.eval("wrap('', '[sound:" + result.getBucketFilename() + "]');") 

gui_hooks.editor_will_show_context_menu.append(addForvoTtsOption)