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

NATIVES = {'af': u'Afrikaans',
 'ar': u'\u0627\u0644\u0639\u0631\u0628\u064a\u0629',
 'be': u'\u0411\u0435\u043b\u0430\u0440\u0443\u0441\u043a\u0430\u044f',
 'bg': u'\u0411\u044a\u043b\u0433\u0430\u0440\u0441\u043a\u0438',
 'ca': u'Catal\xe0',
 'cs': u'\u010ce\u0161tina',
 'cy': u'Cymraeg',
 'da': u'Dansk',
 'de': u'Deutsch',
 'el': u'\u0395\u03bb\u03bb\u03b7\u03bd\u03b9\u03ba\u03ac',
 'en': 'English',
 'es': u'Espa\xf1ol',
 'et': u'Eesti',
 'fa': u'\u0641\u0627\u0631\u0633\u06cc',
 'fi': u'Suomen',
 'fr': u'Fran\xe7ais',
 'ga': u'Gaeilge',
 'gl': u'Galego',
 'hi': u'\u0939\u093f\u0928\u094d\u0926\u0940',
 'hr': u'Hrvatska',
 'hu': u'Magyar',
 'id': u'Indonesia',
 'is': u'\xcdslenska',
 'it': u'Italiano',
 'iw': u'\u05e2\u05d1\u05e8\u05d9\u05ea',
 'ja': u'\u65e5\u672c\u8a9e',
 'ko': u'\ud55c\uad6d\uc5b4',
 'lt': u'Lietuvi\u0161kai',
 'lv': u'Latvie\u0161u',
 'mk': u'\u041c\u0430\u043a\u0435\u0434\u043e\u043d\u0441\u043a\u0438',
 'ms': u'Bahasa Melayu',
 'mt': u'Malti',
 'nl': u'Nederlandse',
 'no': u'Norsk',
 'pl': u'Polska',
 'pt': u'Portugu\xeas',
 'ro': u'Rom\xe2n',
 'ru': u'\u0420\u0443\u0441\u0441\u043a\u0438\u0439',
 'sk': u'Sloven\u010dina',
 'sl': u'Slovenski',
 'sq': u'Shqipe',
 'sr': u'\u0421\u0440\u043f\u0441\u043a\u0438',
 'sv': u'Svenska',
 'sw': u'Kiswahili',
 'th': u'\u0e44\u0e17\u0e22',
 'tl': u'Filipino',
 'tr': u'T\xfcrk\xe7e',
 'uk': u'\u0423\u043a\u0440\u0430\u0457\u043d\u0441\u044c\u043a\u0430',
 'vi': u'Vi\u1ec7t',
 'yi': u'\u05d9\u05d9\u05b4\u05d3\u05d9\u05e9',
 'zh-CN': u'\u4e2d\u6587'}

LANGUAGES_SLUGS_SUPPORTED_FOR_TRANSLATION = dict(
    [
        (slugify(v), k) 
        for k, v in LANGUAGES_SUPPORTED_FOR_TRANSLATION.items()
    ]
)

NATIVE_LANGUAGES_TO_SLUG = dict(
    [
        (NATIVES[v], k)
        for k, v in LANGUAGES_SLUGS_SUPPORTED_FOR_TRANSLATION.items()
    ]
)

