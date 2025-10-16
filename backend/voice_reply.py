# backend/voice_reply.py
from gtts import gTTS
import os

def generate_tamil_reply(text, outpath):
    """
    text: Tamil or English string
    outpath: path to save mp3
    """
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    tts = gTTS(text=text, lang='ta')  # 'ta' for Tamil. For English use 'en'
    tts.save(outpath)
    return outpath
