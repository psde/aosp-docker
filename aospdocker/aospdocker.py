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
import shutil
import pwd
import getpass
import operator
import dockerclient
import aospconfig
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

        self.config = aospconfig.AospDockerConfig(os.path.join(self.base_directory, '.aosp-docker'))

        self.main()

        self.config.write()

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
            print 'Image not found, building...'
            self.client.build_image(dockerfile)

        return True

    def get_container(self):
        container_id = self.config.get('main', 'container-id')
        user = self.config.get('main', 'user')

        if container_id is None or user is None:
            return None

        container = self.client.get_container_by_id(container_id)
        if container is None:
            self.config.remove_option('main', 'container-id')
            return None

        if not container.up:
            print 'Container stopped, starting...',
            self.client.start_container(container.id)
            print 'done.'

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
        root = False

        if cmd == 'root':
            root = True
            if len(sys.argv) == 2:
                print 'Not enough parameters'
                self.print_usage()
                return
            cmd = sys.argv[2]

        if cmd == 'init':
            self.init()
        elif cmd == 'exec' or cmd == 'execute':
            if container is None:
                return self.print_needs_container()
            self.execute(root)
        elif cmd == 'bash':
            if container is None:
                return self.print_needs_container()
            self.bash(root)
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
        user = pwd.getpwnam(getpass.getuser())
        container = self.client.create_container(dockerfile=dockerfile, command='/bin/bash', environment=env, volumes=volumes)

        # Add user to container
        self.client.interactive(container.id, '/bin/bash -c "useradd -b / -d / -M -U -u {uid} -s /bin/bash {user}"'
                                .format(uid=user.pw_uid, user=user.pw_name))

        # Save the environment for the first time
        self.client.interactive(container.id, 'su - {user} -c /bin/bash -c "{saveEnv}"'
                                .format(saveEnv=AospDocker.SaveEnv, user=user.pw_name))

        self.config.set('main', 'container-id', container.id)
        self.config.set('main', 'user', user.pw_name)

        print 'done: {id}'.format(id=container.id)
        print 'You can now use aosp exec [COMMAND]'
        print 'In order to use X11, you need to enable access via \'xhost +\''

        pass

    def execute(self, root=False):
        container = self.get_container()
        user = self.config.get('main', 'user')

        if len(sys.argv) == 2:
            print 'Not enough parameters.'
            print 'Usage: aosp exec [COMMAND...]'
            return

        cmd = " ".join(sys.argv[2:])

        if root:
            self.client.interactive(container.id, '/bin/bash -ic "{cmd}"'.format(cmd=cmd))
        else:
            # Execute command as user
            self.client.interactive(container.id, 'su - {user} -c "{loadEnv} && cd /aosp/{rel_dir} && {cmd} && {saveEnv}"'
                                    .format(user=user, rel_dir=self.relative_directory, loadEnv=AospDocker.LoadEnv, cmd=cmd, saveEnv=AospDocker.SaveEnv))

    def bash(self, root=False):
        container = self.get_container()
        user = self.config.get('main', 'user')

        if root:
            self.client.interactive(container.id, '/bin/bash')
        else:
            # Change directory and save env
            self.client.interactive(container.id, 'su - {user} -c "{loadEnv} && cd /aosp/{rel_dir} && {saveEnv}"'
                                    .format(user=user, rel_dir=self.relative_directory, loadEnv=AospDocker.LoadEnv, saveEnv=AospDocker.SaveEnv))

            # Open a (trapped) shell using rc.bash
            self.client.interactive(container.id, 'su - {user} -c "/bin/bash --rcfile /rc.bash"'
                                    .format(user=user))

    def clean(self):
        container = self.get_container()

        if container is None:
            print 'Container not initialized.'
            self.config.remove_section('main')
            return

        print 'Container found, trying to remove...',
        self.client.remove_container(container.id)
        self.config.remove_section('main')
        print 'done.'

        print 'Removing configuration directory...',
        self.config.remove_configuration()
        print 'done.'

    def info(self):
        container = self.get_container()

        if container is None:
            print 'No container found, use aosp init first.'
            return

        print 'Container Information:'
        print 'Id:\t{id}'.format(id=container.id)
        print 'Image:\t{image}'.format(image=container.image)
        print 'Names:\t{names}'.format(names=container.names)
        print 'Status:\t{status}'.format(status=container.status)

        print '\nAOSP Docker Information:'
        print 'User:\t{user}'.format(user=self.config.get('main', 'user'))
        print 'Dir:\t{dir}'.format(dir=self.base_directory)
        print 'RelDir:\t{dir}'.format(dir=self.relative_directory)
        print 'Config:\t{config}'.format(config=self.config.config_directory)


def cmd():
    AospDocker()

if __name__ == "__main__":
    cmd()
