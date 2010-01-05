import copy
import sys
import dutils, dutils.kvds.utils
from django.utils import simplejson
from kvds.common import dict_to_model, construct_key
from kvds.exceptions import FieldError

class Field(object):
    """ Base Field class, Other Fields extend this one 
    All indexes in the model must be of  type Field
    Used for integer, float, string types
    Parameters:
    - initval : initial value for the field
    - index : if this is True, tyrant will store a a key-value pair with 
    this field as the key and the primary key as the value
    - required : Will raise exception if this field is missing when 
    initializing model
    - primary_index : if this is True, complete model will be saved with
    this field value as key and the model as value, in addition to the id """
    # key name to store meta information in the model
    meta_name = 'fields'
    # prefix to be used with field name when storing in tyrant 
    field_key = ''
    def __init__(self, initval=None, index=False, required=True, primary_index=False):
        self.required = required
        self.primary_index = primary_index
        self.index = index
        if self.primary_index:
            self.index = False
        self.name = ''
        self.val = initval
    
    @classmethod
    def pre_save(cls, model_obj, **kw):
        """ Determines how the field will be stored in data store
        For the base Field class, nothing special needs to be done, the model 
        saves them """
        pass
    
    def make_model(self, k, v, **kw):
        """ Determines how to convert the data from datastore to model
        For base Field class, simply return the value back """
        return v

    @classmethod
    def create(cls, model_obj, mfields, o, **kw):
        """ Initializes the field value for all fields of this(Field) type """
        if not hasattr(model_obj,cls.meta_name):
            return
        d = mfields.keys()
        d.remove('modelname')
        d.remove('key_prefix')
        for prop in d: setattr(model_obj, prop, o.get(prop))
        
    @classmethod
    def data(cls, model_obj, **kw):
        """ Converts objects into dict which is then serialized into json
        and passed to datastore """
        return dict((f.name, f.val) for f in model_obj.fields.values())
    
    def __get__(self, obj, objtype):
        #print "Field getting obj:", obj, "objtype:", objtype
        fo = getattr(obj, self.meta_name) 
        return fo[self.name].val

    def __set__(self, obj, val):
        #print "Field setting ", obj, val
        if self.required:
            if not val:
                raise FieldError("%s is a required Field" % (self.name))
        fo = getattr(obj, self.meta_name) 
        fo[self.name].val = val

    def __deepcopy__(self, memodict):
        obj = copy.copy(self)
        return obj

class ModelBase(type):
    """ Metaclass for kvds models """
    def __new__(cls, name,bases,attrs):
        # create new class
        super_new = super(ModelBase, cls).__new__
        module = attrs.pop('__module__')
        new_class = super_new(cls, name, bases, {'__module__': module})
        
        # adding most needed attributes to save, meta info about instance
        attrs['id'] = Field(primary_index=True)
        attrs['modelname'] = Field(initval=name)
        attrs['key_prefix'] = Field(initval=attrs.get('key_prefix',name))

        # _meta, a dict which saves all fields of one type into array, 
        # with the field meta_name as the key and the array as value
        new_class.add_to_class('_meta', {})
        # field_prefix, a dict which saves fields prefix as keys and
        # the instance as value
        new_class.add_to_class('field_prefix', {})
        for obj_name, obj in attrs.items():
            if isinstance(obj, Field):
                obj.name = obj_name
                if not new_class._meta.get(obj.meta_name):
                    new_class._meta[obj.meta_name] = {}
                new_class._meta[obj.meta_name].update({obj.name:obj})
                #print obj.meta_name, obj.name, obj.field_key , obj
                new_class.field_prefix.update({obj.field_key:obj})
                new_class.add_to_class(obj_name, obj)
            else:
                new_class.add_to_class(obj_name, obj)
            
        return new_class
    
    def add_to_class(cls, name, value):
        setattr(cls, name, value)
    
class Model(object):
    __metaclass__ = ModelBase
    
    def __init__(self, **o):
        self.is_saved = False

        for meta_field in self._meta.keys():
            if not hasattr(self, meta_field):
                setattr(self, meta_field,{})
            for k,v in self._meta[meta_field].items():
                getattr(self, meta_field).update({ k : copy.deepcopy(v)})
        
        if not o.get('id'):
            o['id'] = dutils.uuid()
        
        for fattrs in self._meta.keys():
            mfields = getattr(self,fattrs)
            klass = mfields.values()[0].__class__
            klass.create(self, mfields, o)

    @classmethod
    def filter(cls, **kw):
        pass
        # TODO: - implement filter methods of indexed keys
        # - at kvds implement get_related call, which will get data for all keys inside a list of keys for the given key
        # - method should also have a call where user can ask only for particular set of keys

    @classmethod
    def get(cls, **kw):
        """ Calls kvds, get dict and makes from the dict """
        o = cls.get_dict(**kw)
        m = dict_to_model(cls, o)
        m.is_saved = True
        return m
    
    @classmethod
    def get_dict(cls, **kw):
        """ Calls kvds, gets a dict of the model """
        assert len(kw) == 1
        k, v = kw.items()[0]
        field = cls._meta['fields'].get(k)
        assert field
        assert field.primary_index
        key = construct_key(cls._meta['fields']['key_prefix'].val, k, v)
        o = simplejson.loads(dutils.kvds.utils.kvds(key=key)[key])
        return o

    def __related_data__(self):
        # TODO: Get the complete model in one go with the dict, best optimized if implemented at kvds than here
        pass

    def __data__(self):
        data = {}
        for fattrs in self._meta.keys():
            mfields = getattr(self,fattrs)
            klass = mfields.values()[0].__class__
            data.update(klass.data(self))
        return data

    def save(self):
        """ Saves the model in datastore serialized as json """
        for fattrs in self._meta.keys():
            mfields = getattr(self,fattrs)
            klass = mfields.values()[0].__class__
            klass.pre_save(self)
        data = self.__data__()
        primary_index_keys = []
        for k,f in self.fields.items():
            if f.primary_index:
                v = getattr(self, k)
                key = construct_key(self.key_prefix, k, v)
                primary_index_keys.append(key)
                #print key, "=>", simplejson.dumps(data)
                dutils.kvds.utils.kvds(key=key, value=simplejson.dumps(data))
        for k,f in self.fields.items():
            if f.index:
                v = getattr(self, k)
                index_key = construct_key(self.key_prefix, k, v)
                for pik in primary_index_keys:
                    #print index_key, "=>", pik
                    dutils.kvds.utils.kvds(key=index_key, value=pik)
        self.is_saved = True
