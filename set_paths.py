import sys, path, os

def set_settings(name=""):
    p = path.path(__file__)
    if name:
        c = path.path(name).namebase
    else: 
        c = "settings"
    os.environ["DJANGO_SETTINGS_MODULE"] = "%s.%s" % (p.parent.namebase, c)

def set_paths(f):
    p = path.path(f)
    sys.path.append(str(p.parent.joinpath("../").abspath()))
    sys.path.append(str(p.parent.joinpath("libs/").abspath()))
    set_settings()

set_paths(__file__)

