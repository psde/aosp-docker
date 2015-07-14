#!/usr/bin/env python2

# Copyright 2015 Mathias Garbe <mail@mathias-garbe.de>
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

import os
import sys
import shutil

from configparser import SafeConfigParser


class AospConfig:
    def __init__(self, config_directory):
        self.config_directory = config_directory
        self.config_file = os.path.join(config_directory, 'config')
        self.dirty = False

        self.config = SafeConfigParser()
        self.config.read(self.config_file)

    def write(self):
        if not self.dirty:
            return

        # Check if dir exists
        if os.path.isdir(self.config_directory) == False:
            os.makedirs(self.config_directory)

        with open(self.config_file, 'w') as f:
            self.config.write(f)

    def set(self, section, option, value):
        if not self.config.has_section(section):
            self.config.add_section(section)

        self.config.set(section, option, value)
        self.dirty = True

    def get(self, section, option):
        try:
            return self.config.get(section, option)
        except Exception:
            return None

    def remove_option(self, section, option):
        try:
            self.config.remove_option(section, option)
            self.dirty = True
            return True
        except Exception:
            return False

    def remove_section(self, section):
        try:
            self.config.remove_section(section)
            self.dirty = True
            return True
        except Exception:
            return False

    def remove_configuration(self):
        self.dirty = False
        self.config = SafeConfigParser()
        shutil.rmtree(self.config_directory)
