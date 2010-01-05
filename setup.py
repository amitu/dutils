try:
    from ez_setup import use_setuptools
    use_setuptools()
except ImportError:
    pass

from setuptools import setup, find_packages

setup(
    name="dutils",
    version="0.0.1",
    description="Useful django utilities",
    long_description="""This is a boxy package...""",
    author="Amit Upadhyay",
    author_email="code@amitu.com",
    url="http://github.com/amitu/dutils",
    packages=["dutils"],
)
