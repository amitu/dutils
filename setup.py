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
    long_description="""Reusable django utilities.""",
    author="Amit Upadhyay",
    author_email="code@amitu.com",
    url="http://github.com/amitu/dutils",
    packages=["dutils"],
)
