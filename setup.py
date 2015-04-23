# Copyright 2015 Mathias Garbe <mathias.garbe@inovex.de>
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

from setuptools import setup, find_packages
from codecs import open
from os import path


with open(path.join(path.abspath(path.dirname(__file__)), 'README.md'), encoding='utf-8') as f:
    readme = f.read()

setup(
    name='aospdocker',

    version='0.1.0',

    description='AOSP Docker',
    long_description=readme,

    url='https://github.com/inovex/aosp-docker',

    author='Mathias Garbe',
    author_email='mathias.garbe@inovex.de',

    license='Apache',

    classifiers=[
        'Development Status :: 2 - Pre-Alpha',

        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',

        'Operating System :: POSIX :: Linux',

        'License :: OSI Approved :: Apache Software License',

        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ],

    keywords='aosp android docker development',

    packages=['aospdocker'],

    install_requires=['docker-py'],

    entry_points={
        'console_scripts': [
            'aosp=aospdocker.aospdocker:cmd',
        ],
    },
)