# imports # {{{ 
from django.db import models
from django.utils import simplejson

import time
# }}} 

# Context # {{{ 
class Context(models.Model):
    name = models.CharField(max_length=200, unique=True)
    data = models.TextField("json encoded data")
    delay = models.IntegerField(
        "mimic slow pages, millis to wait", default=-1
    )
    parents = models.ManyToManyField(
        'self', null=True, blank=True, 
        related_name='children', symmetrical=False
    )

    def to_dict(self): 
        """ traverse the parents and get the dict """
        print "to_dict of %s called" % self.name
        d = simplejson.loads(self.data)
        print d
        if self.delay != -1:
            time.sleep(self.delay/1000.0)
        if self.parents.count() == 0: return d
        print self.name, "has parents"
        for parent in self.parents.all():
            print "processing", parent
            for k, v in parent.to_dict().keys():
                print k, v
                if k not in d:
                    print "got new key", k
                    d[k] = v
        return d

    def __unicode__(self): return self.name
# }}} 

# Page # {{{ 
class Page(models.Model):
    name = models.CharField("name for the type", max_length=200)
    template = models.CharField("template to use", max_length=200)
    url = models.CharField("url to bind to, can be regex", max_length=200)

    contexts = models.ManyToManyField(Context, null=True)

    def __unicode__(self): return self.name
# }}} 
