#!/usr/bin/env python2

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

import os
import sys
import ConfigParser
import operator
import dockerclient
from dockerfile import Dockerfile


class AospDocker:
    LoadEnv = 'source /env.bash'
    SaveEnv = 'declare -p | sed -e \'/declare -[a-z]*r/d\' > /env.bash && declare -f >> /env.bash'

    def __init__(self):
        self.versions = Dockerfile.build_versions()
        self.client = dockerclient.Client()

        self.base_directory = self.find_config_directory()
        if self.base_directory is None:
            self.base_directory = os.getcwd()

        self.relative_directory = os.path.relpath(os.getcwd(), self.base_directory)

        config_dir = self.base_directory + '/.aosp-docker/'
        config_file = config_dir + 'config'

        # Check if dir exists
        if os.path.isdir(config_dir) == False:
            os.makedirs(config_dir)

        self.config = ConfigParser.SafeConfigParser()
        self.config.read(config_file)
        try:
            self.config.add_section('main')
        except Exception:
            pass

        self.main()

        with open(config_file, 'w') as f:
            self.config.write(f)

    def find_config_directory(self):
        current_path = os.getcwd()
        old_path = current_path
        while True:
            if os.path.isfile(os.path.join(current_path, '.aosp-docker', 'config')) == True:
                return current_path

            current_path = os.path.abspath(os.path.join(current_path, os.pardir))
            if old_path == current_path:
                break
            old_path = current_path

        return None

    def check_or_build_image(self, dockerfile):
        image = None
        images = self.client.get_images()
        try:
            image = filter(lambda image: image.repo.startswith(dockerfile.get_image_name()), images)[0]
        except Exception:
            pass

        if image is None:
            self.client.build_image(dockerfile)

        return True

    def get_container(self):
        try:
            container_id = self.config.get('main', 'container-id')
        except ConfigParser.NoOptionError:
            return None

        if container_id == '-1':
            return None

        container = self.client.get_container_by_id(container_id)
        if container is None:
            self.config.set('main', 'container-id', '-1')
            return None

        if not container.up:
            print 'Container stopped, starting ...'
            self.client.startContainer(container.id)

        return container

    def print_needs_container(self):
        print 'Container not found, please use \'aosp init\' first'

    def print_usage(self):
        print 'Usage: aosp [COMMAND] [arg...]'
        print 'Commands:'
        print '\tinit\tInitialize a container in current directory (should be AOSP dir)'
        print '\texec\tExecutes a command inside the aosp build container'
        print '\tbash\tStarts a bash shell inside the container'
        print '\tclean\tRemoves container'
        print '\tinfo\tShows information about the aosp container'

    def main(self):
        if len(sys.argv) == 1:
            print 'Not enough parameters'
            self.print_usage()
            return

        container = self.get_container()

        cmd = sys.argv[1]

        if cmd == 'init':
            self.init()
        elif cmd == 'exec' or cmd == 'execute':
            if container is None:
                return self.print_needs_container()
            self.execute()
        elif cmd == 'bash':
            if container is None:
                return self.print_needs_container()
            self.bash()
        elif cmd == 'clean':
            self.clean()
        elif cmd == 'info':
            self.info()
        else:
            print 'Unrecognized command'
            self.print_usage()

    def print_init_usage(self):
        print 'Usage: aosp init [VERSION]'
        print 'Supported versions: '
        for key, value in sorted(self.versions.items(), key=operator.itemgetter(0)):
            print "\t{key}\t\tbased on {base}".format(key=key, base=value.base)

    def init(self):
        if len(sys.argv) == 2:
            print 'Not enough parameters'
            self.print_init_usage()
            return

        version = sys.argv[2]
        if version not in self.versions:
            print 'Did not recognize Android version.'
            self.print_init_usage()
            return

        dockerfile = self.versions[version]
        self.check_or_build_image(dockerfile)

        container = self.get_container()

        if container is not None:
            print 'Container already initialized.'
            return

        print 'Setting up new container...',

        volumes = {'/tmp/.X11-unix': '/tmp/.X11-unix', os.getcwd(): '/aosp'}
        env = ['DISPLAY=unix{display}'.format(display=os.environ['DISPLAY'])]
        container = self.client.create_container(dockerfile=dockerfile, command='/bin/bash', environment=env, volumes=volumes)

        self.client.interactive(container.id, '/bin/bash -ic "{saveEnv}"'.format(saveEnv=AospDocker.SaveEnv))

        self.config.set('main', 'container-id', container.id)
        print 'done: {id}'.format(id=container.id)
        print 'You can now use aosp exec [COMMAND]'
        print 'In order to use X11, you need to enable access via \'xhost +\''

        pass

    def execute(self):
        container = self.get_container()

        if len(sys.argv) == 2:
            print 'Not enough parameters.'
            print 'Usage: aosp exec [COMMAND...]'
            return

        cmd = " ".join(sys.argv[2:])

        self.client.interactive(container.id, '/bin/bash -ic "{loadEnv} && cd /aosp/{rel_dir} && {cmd} && {saveEnv}"'.format(rel_dir=self.relative_directory, loadEnv=AospDocker.LoadEnv, cmd=cmd, saveEnv=AospDocker.SaveEnv))

    def bash(self):
        container = self.get_container()
        self.client.interactive(container.id, '/bin/bash -ic "{loadEnv} && cd /aosp/{rel_dir} && {saveEnv}"'.format(rel_dir=self.relative_directory, loadEnv=AospDocker.LoadEnv, saveEnv=AospDocker.SaveEnv))
        self.client.interactive(container.id, '/bin/bash --rcfile /rc.bash')

    def clean(self):
        container = self.get_container()

        if container is None:
            print 'Container not initialized.'
            self.config.set('main', 'container-id', '-1')
            return

        print 'Container found, trying to remove...'
        self.client.remove_container(container.id)

        self.config.set('main', 'container-id', '-1')
        print 'done.'

    def info(self):
        container = self.get_container()

        if container is None:
            print 'No container found, use aosp init first.'
            return

        print 'Container Information'
        print 'Id:\t{id}'.format(id=container.id)
        print 'Dir:\t{dir}'.format(dir=self.base_directory)
        print 'RelDir:\t{dir}'.format(dir=self.relative_directory)
        print 'Image:\t{image}'.format(image=container.image)
        print 'Names:\t{names}'.format(names=container.names)
        print 'Status:\t{status}'.format(status=container.status)

if __name__ == "__main__":
    aosp = AospDocker()
