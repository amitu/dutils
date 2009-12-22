class attrdict(dict):
    def __init__(self, *args, **kw):
        dict.__init__(self, *args, **kw)
        self.__dict__ = self

if __name__ == "__main__":
    import set_paths
    from path import path
    from kvds_server import *
    APP_DIR = path(".")
    #DEBUG = True
    #TEMPLATE_DIRS = (".", )
    INSTALLED_APPS = ('dutils',)
    from django.core.management import execute_manager
    execute_manager(attrdict(locals()))

