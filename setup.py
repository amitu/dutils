try:
    from ez_setup import use_setuptools
except ImportError:
    pass
else:
    use_setuptools()

from setuptools import setup, find_packages

setup(
    name="dutils",
    version="0.0.2",
    description="Useful django utilities",
    long_description="""Reusable django utilities.""",
    author="Amit Upadhyay",
    author_email="code@amitu.com",
    url="http://github.com/amitu/dutils",
    packages=["dutils"],
)
