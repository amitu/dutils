from distutils.core import setup
from distutils.command.install_data import install_data
from distutils.command.install import INSTALL_SCHEMES
import sys, os

class osx_install_data(install_data):
    # On MacOS, the platform-specific lib dir is /System/Library/Framework/Python/.../
    # which is wrong. Python 2.5 supplied with MacOS 10.5 has an Apple-specific fix
    # for this in distutils.command.install_data#306. It fixes install_lib but not
    # install_data, which is why we roll our own install_data class.

    def finalize_options(self):
        # By the time finalize_options is called, install.install_lib is set to the
        # fixed directory, so we set the installdir to install_lib. The
        # install_data class uses ('install_data', 'install_dir') instead.
        self.set_undefined_options('install', ('install_lib', 'install_dir'))
        install_data.finalize_options(self)

if sys.platform == "darwin":
    cmdclasses = {'install_data': osx_install_data}
else:
    cmdclasses = {'install_data': install_data}

def fullsplit(path, result=None):
    """
    Split a pathname into components (the opposite of os.path.join) in a
    platform-neutral way.
    """
    if result is None:
        result = []
    head, tail = os.path.split(path)
    if head == '':
        return [tail] + result
    if head == path:
        return result
    return fullsplit(head, [tail] + result)

# Compile the list of packages available, because distutils doesn't have
# an easy way to do this.
packages, data_files = [], []
root_dir = os.path.dirname(__file__)
if root_dir != '':
    os.chdir(root_dir)
dutils_dir = 'dutils'

for dirpath, dirnames, filenames in os.walk(dutils_dir):
    # Ignore dirnames that start with '.'
    for i, dirname in enumerate(dirnames):
        if dirname.startswith('.'): del dirnames[i]
    if '__init__.py' in filenames:
        packages.append('.'.join(fullsplit(dirpath)))
    elif filenames:
        data_files.append([dirpath, [os.path.join(dirpath, f) for f in filenames]])

import dutils

from distutils.command.install import INSTALL_SCHEMES 
for scheme in INSTALL_SCHEMES.values():
        scheme['data'] = scheme['purelib']
setup(
    name="dutils",
    version=dutils.VERSION,
    description="Useful dutils utilities",
    long_description="""Reusable dutils utilities.

Documentation: http://packages.python.org/dutils/
    """,
    author="Amit Upadhyay",
    author_email="code@amitu.com",
    url="http://github.com/amitu/dutils",
    packages = packages,
    cmdclass = cmdclasses,
    data_files = data_files,
)

"""
    classifiers = [
        ""Development Status :: 3 - Alpha
Environment :: Web Environment
Framework :: dutils
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
