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

import os, sys, ConfigParser

import DockerClient

from dockerfile import Dockerfile

class AospDocker:
    LoadEnv = 'source /env.bash'
    SaveEnv = 'declare -p | sed -e \'/declare -[a-z]*r/d\' > /env.bash && declare -f >> /env.bash'

    def __init__(self):
        self.versions = Dockerfile.buildVersions()
        self.client = DockerClient.Client()

        config_dir = os.getcwd() + '/.aosp-docker/'
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

    def checkOrBuildImage(self, dockerfile):
        image = None
        images = self.client.getImages()
        try:
            image = filter(lambda image: image.repo.startswith(dockerfile.getImageName()), images)[0]
        except Exception:
            pass

        if image is None:
            self.client.buildImage(dockerfile)

        return True

    def getContainer(self):
        try:
            container_id = self.config.get('main', 'container-id')
        except ConfigParser.NoOptionError:
            return None

        if container_id == '-1':
            return None

        container = self.client.getContainerById(container_id)
        if container is None:
            return None

        if container.up == False:
            print 'Container stopped, starting ...'
            self.client.startContainer(container.id)

        return container

    def needsContainer(self):
        container = self.getContainer()

        if container is None:
            print 'Container not found, please use \'aosp init\' first'
            return False
        return True

    def printUsage(self):
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
            self.printUsage()
            return

        cmd = sys.argv[1]

        if cmd == 'init':
            self.init()
        elif cmd == 'exec' or cmd == 'execute':
            if self.needsContainer() == False:
                return
            self.execute()
        elif cmd == 'bash':
            if self.needsContainer() == False:
                return
            self.bash()
        elif cmd == 'clean':
            self.clean()
        elif cmd == 'info':
            self.info()
        else:
            print 'Unrecognized command'
            self.printUsage()

    def printInitUsage(self):
        print 'Usage: aosp init [VERSION]'
        print 'Supported versions: '
        for key, value in self.versions.iteritems() :
            print "\t{key}\t\tbased on {base}".format(key=key, base=value.base)

    def init(self):
        if len(sys.argv) == 2:
            print 'Not enough parameters'
            self.printInitUsage()
            return

        version = sys.argv[2]
        if version not in self.versions:
            print 'Did not recognize android version'
            self.printInitUsage()
            return

        dockerfile = self.versions[version]
        self.checkOrBuildImage(dockerfile)

        container = self.getContainer()

        if container is not None:
            print 'Container already initialized'
            return

        print 'Setting up new container ...'

        volumes = {'/tmp/.X11-unix': '/tmp/.X11-unix', os.getcwd(): '/aosp'}
        env = ['DISPLAY=unix{display}'.format(display=os.environ['DISPLAY'])]
        container = self.client.createContainer(dockerfile=dockerfile, command='/bin/bash', environment=env, volumes=volumes)
        id = container.id

        self.client.interactive(id, '/bin/bash -ic "cd /aosp && {saveEnv}"'.format(id=id, saveEnv=AospDocker.SaveEnv))
        
        self.config.set('main', 'container-id', id)
        print 'done: {id}'.format(id=id)
        print 'You can now use aosp exec [COMMAND]'
        print 'In order to use X11, you need to enable access via \'xhost +\''

        pass

    def execute(self):
        container = self.getContainer()

        if len(sys.argv) == 2:
            print 'Not enough parameters.'
            print 'Usage: aosp exec [COMMAND...]'
            return

        if container.up == False:
            print 'Container {id} down, starting ...'.format(id=container.id)
            self.client.startContainer(container.id)

        cmd = " ".join(sys.argv[2:])

        self.client.interactive(container.id, '/bin/bash -ic "{loadEnv} && cd \$PWD && {cmd} && {saveEnv}"'.format(id=container.id, loadEnv=AospDocker.LoadEnv, cmd=cmd, saveEnv=AospDocker.SaveEnv))

    def bash(self):
        container = self.getContainer()
        self.client.interactive(container.id, '/bin/bash --rcfile /rc.bash')

    def clean(self):
        container = self.getContainer()

        if container is None:
            print 'Container not initialized.'
            self.config.set('main', 'container-id', '-1')
            return

        print 'Container found, trying to remove...'
        self.client.removeContainer(container.id)

        self.config.set('main', 'container-id', '-1')
        print 'done.'

    def info(self):
        container = self.getContainer()

        if container is None:
            print 'No container found, use aosp init first.'
            return

        print 'Container Information'
        print 'Id:\t{id}'.format(id=container.id)
        print 'Image:\t{image}'.format(image=container.image)
        print 'Names:\t{names}'.format(names=container.names)
        print 'Status:\t{status}'.format(status=container.status)

if __name__ == "__main__":
    aosp = AospDocker()
