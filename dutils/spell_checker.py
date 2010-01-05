import re, collections

def words(text): return re.findall('[a-z]+', text.lower()) 

def train(features):
    model = collections.defaultdict(lambda: 1)
    for f in features:
        model[f] += 1
    return model

alphabet = 'abcdefghijklmnopqrstuvwxyz'

def edits1(word):
   s = [(word[:i], word[i:]) for i in range(len(word) + 1)]
   deletes    = [a + b[1:] for a, b in s if b]
   transposes = [a + b[1] + b[0] + b[2:] for a, b in s if len(b)>1]
   replaces   = [a + c + b[1:] for a, b in s for c in alphabet if b]
   inserts    = [a + c + b     for a, b in s for c in alphabet]
   return set(deletes + transposes + replaces + inserts)

def known_edits2(word, NWORDS):
    return set(e2 for e1 in edits1(word) for e2 in edits1(e1) if e2 in NWORDS)

def known(words, NWORDS): return set(w for w in words if w in NWORDS)

# SpellChecker # {{{ 
class SpellChecker(object):

    def __init__(self, fname_or_object):
        self.train(fname_or_object)

    def train(self, fname_or_object):
        if hasattr(fname_or_object, "read"):
            content = fname_or_object.read()
        else:
            content = file(fname_or_object).read()
        self.NWORDS = train(words(content))

    def correct(self, word):
        candidates = (
            known([word], self.NWORDS) or 
            known(edits1(word), self.NWORDS) or 
            known_edits2(word, self.NWORDS) or [word]
        )
        return max(candidates, key=self.NWORDS.get)
# }}} 
