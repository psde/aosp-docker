#!/bin/python
import os, sys, subprocess, ConfigParser

from dockerfile import Dockerfile

class AospDocker:
    LoadEnv = 'source /env.bash'
    SaveEnv = 'declare -p | sed -e \'/declare -[a-z]*r/d\' > /env.bash && declare -f >> /env.bash'

    def __init__(self):
        self.versions = Dockerfile.buildVersions()

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
        count = '0'
        try:
            count = subprocess.check_output('docker images | grep -c {name}'.format(name=dockerfile.getImageName()), shell=True).strip()
        except Exception:
            pass

        if count != '1':
            cmd = 'docker build -t {name} -'.format(name=dockerfile.getImageName())
            p = subprocess.Popen(cmd.split(" "), stdin=subprocess.PIPE, stderr=subprocess.STDOUT)    
            p.communicate(input=b'' + dockerfile.buildDockerfile())[0]

        return True

    def getContainer(self):
        try:
            container_id = self.config.get('main', 'container-id')
        except ConfigParser.NoOptionError:
            return False, -1

        if container_id == '-1':
            return False, -1

        try:
            count = subprocess.check_output('docker ps -a | grep -c {id}'.format(id=container_id[:11]), shell=True).strip()
        except Exception:
            return False, -1

        if count != '1':
            return False, container_id

        return True, container_id

    def needsContainer(self):
        s, id = self.getContainer()

        if s == False:
            if id == -1:
                print 'Container not found, please use \'aosp init\' first'
            else:
                print 'Container id found but container not present, please use \'aosp init\' first'
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

        s, id = self.getContainer()

        if s == True:
            print 'Container already initialized'
            return

        if id != -1:
            print 'Old container found, trying to remove'
            subprocess.check_output('docker rm -f {id}'.format(id=id), shell=True)

        print 'Setting up new container ...'
        id = subprocess.check_output('docker run -td --net host -e DISPLAY=unix$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix -v "$PWD:/aosp" {name} /bin/bash'.format(name=dockerfile.getImageName()), shell=True).strip()
        subprocess.call('docker exec -it {id} /bin/bash -ic "cd /aosp && {saveEnv}"'.format(id=id, saveEnv=AospDocker.SaveEnv), shell=True)
        self.config.set('main', 'container-id', id)
        print 'done: {id}'.format(id=id)
        print 'You can now use aosp exec [COMMAND]'
        print 'In order to use X11, you need to enable access via \'xhost +\''

        pass

    def execute(self):
        s, id = self.getContainer()

        if len(sys.argv) == 2:
            print 'Not enough parameters.'
            print 'Usage: aosp exec [COMMAND...]'
            return

        cmd = " ".join(sys.argv[2:])

        subprocess.call('docker exec -it {id} /bin/bash -ic "{loadEnv} && cd \$PWD && {cmd} && {saveEnv}"'.format(id=id, loadEnv=AospDocker.LoadEnv, cmd=cmd, saveEnv=AospDocker.SaveEnv), shell=True)

        return

    def bash(self):
        s, id = self.getContainer()
        subprocess.call('docker exec -it {id} /bin/bash --rcfile /rc.bash '.format(id=id), shell=True)

    def clean(self):
        s, id = self.getContainer()

        if s == False:
            print 'Container not initialized.'
            self.config.set('main', 'container-id', '-1')
            return

        if id != -1:
            print 'Container found, trying to remove...'

            try:
                subprocess.check_output('docker rm -f ' + id, shell=True)
            except Exception:
                pass

            self.config.set('main', 'container-id', '-1')
            print 'done.'

    def info(self):
        s, id = self.getContainer()

        if s == False or id == -1:
            print 'No container found'
            return

        print 'Container ID: {id}'.format(id=id)

        pass

if __name__ == "__main__":
    aosp = AospDocker()
