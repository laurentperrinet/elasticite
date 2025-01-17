#!/usr/bin/env python
# -*- coding: utf8 -*-

from setuptools import setup, find_packages

NAME = "elasticite"
version = "0.1.1"

setup(
    name = NAME,
    version = version,
    packages=find_packages('elasticite', exclude='docs'),
    package_dir = {'': 'elasticite'},
    author = "Laurent Perrinet INT - CNRS",
    author_email = "Laurent.Perrinet@univ-amu.fr",
    description = "Elasticité: une expérience plastique avec Etienne Rey.",
    long_description=open("README.md").read(),
    license = "GPLv2",
    keywords = ('computational neuroscience', 'simulation', 'analysis', 'visualization', 'computer vision'),
    url = 'https://github.com/meduz/' + NAME, # use the URL to the github repo
    download_url = 'https://github.com/meduz/' + NAME + '/tarball/' + version,
    classifiers = ['Development Status :: 3 - Alpha',
                   'Environment :: Console',
                   'License :: OSI Approved :: GNU General Public License (GPL)',
                   'Operating System :: POSIX',
                   'Topic :: Scientific/Engineering',
                   'Topic :: Utilities',
                   'Programming Language :: Python :: 2',
                   'Programming Language :: Python :: 2.7',
                   'Programming Language :: Python :: 3',
                   'Programming Language :: Python :: 3.4',
                  ],
     )
