def dict_to_model(klass, d):
    """ Takes a serialized dict object and converts it into object instance
    - klass : class used to deserialize the dict
    - d : serialized dict data to create object
    """
    o = {}
    for k,v in d.items():
        fkey = k.split('__')[0]
        field_obj = klass.field_prefix.get('%s__' % fkey)
        if not field_obj:
            field_obj = klass.field_prefix['']
            fname = fkey
        else:
            fname = k.split('__')[1]
        fobj = field_obj.make_model(fname,v)
        o.update({str(fname):fobj})
    obj = klass(**o)
    return obj

def construct_key(key_prefix, keyname, key):
    return ("%s.%s__%s" % (key_prefix, keyname, key)).lower()
