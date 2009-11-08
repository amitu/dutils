import re
import sys
import urllib
from django.utils import simplejson
from django.template.defaultfilters import slugify

LANGUAGES_SUPPORTED_FOR_TRANSLATION = { 
    "af": "Afrikaans", "sq":"Albanian", "ar": "Arabic", "be": "Belarusian", 
    "bg": "Bulgarian", "ca": "Catalan", "zh-CN":"Chinese", "hr": "Croatian",
    "cs":"Czech", "da":"Danish", "nl":"Dutch", "en": "English", 
    "et": "Estonian", "tl": "Filipino", "fi": "Finnish", "fr": "French", 
    "gl": "Galician", "de": "German", "el": "Greek", "iw": "Hebrew", 
    "hi": "Hindi", "hu": "Hungarian", "is": "Icelandic", "id": "Indonesian", 
    "ga": "Irish", "it": "Italian", "ja": "Japanese", "ko": "Korean", 
    "lv": "Latvian", "lt": "Lithuanian", "mk": "Macedonian", "ms": "Malay",
    "mt": "Maltese", "no": "Norwegian", "fa": "Persian", "pl": "Polish",
    "pt": "Portuguese", "ro": "Romanian", "ru": "Russian", "sr": "Serbian", 
    "sk": "Slovak", "sl": "Slovenian", "es": "Spanish", "sw": "Swahili", 
    "sv": "Swedish", "th": "Thai", "tr": "Turkish", "uk": "Ukrainian", 
    "vi": "Vietnamese", "cy": "Welsh", "yi": "Yiddish"
}

LANGUAGES_SLUGS_SUPPORTED_FOR_TRANSLATION = dict(
    [
        (slugify(v), k) 
        for k, v in LANGUAGES_SUPPORTED_FOR_TRANSLATION.items()
    ]
)

baseUrl = "http://ajax.googleapis.com/ajax/services/language/translate"

def getSplits(text,splitLength=4500):
    '''
    Translate Api has a limit on length of text(4500 characters) that can be translated at once, 
    '''
    return (text[index:index+splitLength] for index in xrange(0,len(text),splitLength))


def translate(text, to='hi', src='en'):
    '''
    A Python Wrapper for Google AJAX Language API:
    * Uses Google Language Detection, in cases source language is not provided with the source text
    * Splits up text if it's longer then 4500 characters, as a limit put up by the API
    '''

    if to == src: return text

    if to not in LANGUAGES_SUPPORTED_FOR_TRANSLATION:
        to = LANGUAGES_SLUGS_SUPPORTED_FOR_TRANSLATION[to]

    if src not in LANGUAGES_SUPPORTED_FOR_TRANSLATION:
        src = LANGUAGES_SLUGS_SUPPORTED_FOR_TRANSLATION[src]

    params = ({'langpair': '%s|%s' % (src, to),
             'v': '1.0'
             })
    retText=''
    for text in getSplits(text):
            params['q'] = text
            resp = simplejson.load(urllib.urlopen('%s' % (baseUrl), data = urllib.urlencode(params)))
            try:
                    retText += resp['responseData']['translatedText']
            except:
                    raise
    return retText


def test():
    msg = "      Write something You want to be translated to Hindi,\n"\
        "      Enter ctrl+c to exit"
    print msg
    while True:
        text = raw_input('#>  ')
        retText = translate(text)
        print retText
        

if __name__=='__main__':
    try:
        test()
    except KeyboardInterrupt:
        print "\n"
        sys.exit(0)
