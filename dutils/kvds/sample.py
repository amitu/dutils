from kvds.models import *
from kvds.fields import *

class Amodel(Model):
    key_prefix = 'kvds__a__comment'
    a1 = Field()
    a2 = Field()
    a3 = Field()

class Bmodel(Model):
    key_prefix = 'kvds__b__comment'
    b1 = Field()
    b2 = Field()
    ba = ForeignKey(Amodel)

class Cmodel(Model):
    key_prefix = 'kvds__c__comment'
    c1 = Field()
    c2 = Field()
    c3 = Field()

class Composite(Model):
    key_prefix = 'kvds__composite'
    compa = Field()
    compb = ManyToManyField(Cmodel)
    compc = ForeignKey(Bmodel)
    pid = Field(index=True)

a1item = Amodel(a1='itema1a1', a2='itema1a2', a3='itema1a3')
b1item = Bmodel(b1='itema2a1', b2='itema2a2', ba=a1item)
c1item = Cmodel(c1='itemc1c1', c2='itemc1c2', c3='itemc1c3')
c2item = Cmodel(c1='itemc2c1', c2='itemc2c2', c3='itemc2c3')

comp_obj = Composite(compa='Random values here', compb=[c1item,c2item], compc=b1item, pid="23413423")
comp_obj.save()

comp_new = Composite.get(id=comp_obj.id)
