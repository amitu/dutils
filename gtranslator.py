# imports # {{{ 
import re
import sys
import urllib
from django.utils import simplejson
from dutils.gtranslator_constants import *
# }}} 

baseUrl = "http://ajax.googleapis.com/ajax/services/language/translate"

# get_splits 
def get_splits(text, splitLength=4500):
    '''
    Translate Api has a limit on length of text(4500 characters) that can be
    translated at once.
    '''
    return (
        text[index:index+splitLength] 
        for index in xrange(0,len(text),splitLength)
    )

def translate(text, to='hi', src='en'):
    '''
    A Python Wrapper for Google AJAX Language API:

    * Uses Google Language Detection, in cases source language is not
      provided with the source text
    * Splits up text if it's longer then 4500 characters, as a limit put up
      by the API

    '''

    if to == src: return text

    if to not in LANGUAGES_SUPPORTED_FOR_TRANSLATION:
        to = LANGUAGES_SLUGS_SUPPORTED_FOR_TRANSLATION[to]

    if src not in LANGUAGES_SUPPORTED_FOR_TRANSLATION:
        src = LANGUAGES_SLUGS_SUPPORTED_FOR_TRANSLATION[src]

    params = {'langpair': '%s|%s' % (src, to), 'v': '1.0' }
    retText=''
    for text in get_splits(text):
        params['q'] = text
        params = urllib.urlencode(
            dict([(k, v.encode('utf-8')) for k, v in params.items()])
        )
        try:
            resp = simplejson.load(
                urllib.urlopen('%s' % (baseUrl), data = params)
            )
        except ValueError:
            return text
        if resp['responseData']:
            retText += resp['responseData']['translatedText']
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
