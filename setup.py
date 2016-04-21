#!/usr/bin/env python
# Copyright 2016 Zoltan Beck
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Kumbh Mela serial device reader"""

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

exec(open('kumbhserial/version.py').read())

setup(name='kumbhserial',
      version=__version__,
      description=__doc__,
      author='Zoltan Beck',
      author_email='zb1f12@soton.ac.uk',
      packages=['kumbhserial'],
      install_requires=['pyserial', 'docopt'],
      tests_require=['nose', 'pyflakes', 'pep8'],
      entry_points={
        'console_scripts': [
            'kumbhdownload = kumbhserial.main:download',
            'kumbhsniffer = kumbhserial.main:sniffer'
        ]
      },
      classifiers=[
        'Environment :: Console',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
      ],
      )
