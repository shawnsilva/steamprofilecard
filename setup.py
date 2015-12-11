#!/usr/bin/env python
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Copyright (C) 2011-2015  Shawn Silva
# ------------------------------------
# This file is part of SteamProfileCard
#
# SteamProfileCard is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

"""Setuptools installer for SteamProfileCard"""

from setuptools import setup

import steamprofilecard

def long_description():
      with open('README.rst') as f:
            readme = f.read()
      with open('CHANGELOG.rst') as f:
            changelog = f.read()
      return readme + changelog

setup(name='steamprofilecard',
      version=steamprofilecard.__version__,
      description='steamprofilecard will make a gamer card image out of a given steam profile.',
      author='Shawn Silva',
      author_email='ssilva@jatgam.com',
      url='https://github.com/shawnsilva/steamprofilecard',
      packages=['steamprofilecard'],
      long_description=long_description(),
      keywords='steam valve api web user group profile gamer card image',
      license='GNU GPL v3',
      platforms='Unix, Windows',
      test_suite='steamprofilecard.test',
      classifiers=[
            'Development Status :: 4 - Beta',

            'Intended Audience :: Developers',

            'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',

            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 2.6',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.2',
            'Programming Language :: Python :: 3.3',
            'Programming Language :: Python :: 3.4',
            'Programming Language :: Python :: 3.5',

            'Natural Language :: English',
            'Operating System :: OS Independent',
            'Topic :: Internet',
      ],
     )
