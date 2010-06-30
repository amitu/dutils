from fabric.api import *

def all():
    print "Current version: %s" % file("VERSION").read().strip()
    assert_clean()
    bump_version()
    update_init_py()
    update_docs_conf_py()
    commit_and_push()
    build_docs()
    upload_docs()
    release()
    print "Pushed: %s" % file("VERSION").read().strip()

def assert_clean():
    "make sure there are no pending changes to be committed"
    # returns error if there are pending changes, halts script
    if local("git diff"):
        abort("There are pending changes to be committed.")
    if local("git diff --cached"):
        abort("There are pending changes to be committed.")

def bump_version():
    "increment the version"
    current_version = file("VERSION").read().strip()
    parts = [int(p) for p in current_version.split(".")]
    parts[-1] += 1
    next_version = ".".join([str(p) for p in parts])
    file("VERSION", "w").write(next_version+"\n")
    return next_version

def update_init_py():
    current_version = file("VERSION").read().strip()
    file("dutils/__init__.py", "w").write(
        file("dutils/__init__.py.templ").read().replace(
            "__VERSION__", current_version
        )
    )

def update_docs_conf_py():
    current_version = file("VERSION").read().strip()
    file("docs/conf.py", "w").write(
        file("docs/conf.py.templ").read().replace(
            "__VERSION__", current_version
        )
    )

def commit_and_push():
    local('git commit -a -m "release %s"' % file("VERSION").read().strip())
    local('git push')

def build_docs():
    local("cp setup_docs.py setup.py")
    local("python setup.py build_sphinx")
    local("open docs/build/html/index.html")
    local("cp setup_main.py setup.py")

def upload_docs():
    local("cp setup_docs.py setup.py")
    local("python setup.py upload_sphinx")
    local("open http://packages.python.org/dutils/")
    local("cp setup_main.py setup.py")

def release():
    local("python setup.py sdist --formats=gztar,zip upload")
