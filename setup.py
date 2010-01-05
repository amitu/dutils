from ez_setup import use_setuptools
use_setuptools()
from setuptools import setup, find_packages

setup(
    name="dutils",
    version="0.1dev",
    description="Useful django utilities",
    long_description="""This is a boxy package...""",
    author="Amit Upadhyay",
    author_email="code@amitu.com",
    url="http://github.com/amitu/dutils",
    packages=[ p for p in find_packages("..") if p.startswith("dutils") ],
    package_dir = {'': '..'},
)
