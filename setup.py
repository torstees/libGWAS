import ez_setup
ez_setup.use_setuptools()

import setuptools
import os
import sys


# Grab the version from the application itself for consistency
import mvtest
import meanvar

# Use the README as the long description
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setuptools.setup(name="mvtest",
    version=mvtest.__version__,
    author="Eric Torstenson",
    author_email="eric.s.torstenson@vanderbilt.edu",
    url="TBD",
    packages=["meanvar","tests","pygwas"],
    license="TBD",
    scripts=["mvtest.py"],
    install_requires=["scipy","numpy"],
    long_description=read('README.md'),
    test_suite='tests',
    package_data={'meanvar/tests/bedfiles':['*'],
                  'doc':['*']},
    classifiers=[
        "Development Status :: 3 - Beta",
        "Topic :: Utilities",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Topic :: Software Development :: Libraries",
        "Programming Language :: Python :: 2.7"
    ],
)
