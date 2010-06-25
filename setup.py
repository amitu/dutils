try:
    from ez_setup import use_setuptools
except ImportError:
    pass
else:
    use_setuptools()

from setuptools import setup, find_packages

import dutils

setup(
    name="dutils",
    version=dutils.VERSION,
    description="Useful django utilities",
    long_description="""Reusable django utilities.

Documentation: http://packages.python.org/dutils/
    """,
    author="Amit Upadhyay",
    author_email="code@amitu.com",
    url="http://github.com/amitu/dutils",
    packages=[
        "dutils", "dutils.kvds", "dutils.kvds_server", "dutils.management", 
        "dutils.management.commands", "dutils.templatetags",
    ],
    #package_dir={'dutils': "."},
)

"""
    classifiers = [
        ""Development Status :: 3 - Alpha
Environment :: Web Environment
Framework :: Django
Intended Audience :: Developers
License :: OSI Approved :: BSD License
Natural Language :: English
Operating System :: POSIX
Programming Language :: Python
Topic :: Internet :: WWW/HTTP :: Dynamic Content
Topic :: Software Development :: Libraries :: Application Frameworks
Topic :: Utilities"" . splitlines()
    ],
"""
