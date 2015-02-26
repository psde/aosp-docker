#!/bin/python
import os, sys, subprocess, ConfigParser

class Dockerfile():
    def __init__(self, version, base, packages, java, misc=''):
        self.version = version
        self.base = base
        self.packages = packages
        self.java = java
        self.misc = misc

    def getImageName(self):
        return 'aosp-docker-{version}'.format(version=self.version)

    def buildDockerfile(self):
        misc = ''
        if self.misc != '':
            misc = "RUN {cmd}".format(cmd=self.misc)
        d = ("FROM {base}\n"
             "MAINTAINER Mathias Garbe <mgarbe@inovex.de>\n"
             "RUN touch /env.bash && echo 'source /env.bash' > /rc.bash && echo 'cd $PWD' >> /rc.bash && echo \"trap \\\"declare -p | sed -e '/declare -[a-z]*r/d' > /env.bash && declare -f >> /env.bash\\\" EXIT\" >> /rc.bash\n"
             "RUN apt-get update\n"
             "RUN {java}\n"
             "RUN echo \"dash dash/sh boolean false\" | debconf-set-selections && dpkg-reconfigure -p critical dash\n"
             "RUN apt-get install -y bash-completion vim wget {packages}\n"
             "ADD https://commondatastorage.googleapis.com/git-repo-downloads/repo /usr/local/bin/\n"
             "RUN chmod 755 /usr/local/bin/*\n"
             "{misc}\n"
             "VOLUME [\"/tmp/ccache\", \"/aosp\"]\n"
             "ENV USE_CCACHE 1\n"
             "ENV CCACHE_DIR /tmp/ccache\n"
             "RUN apt-get clean && rm -rf /var/lib/apt/lists/* /var/tmp/*\n").format(base=self.base, java=self.java, packages=self.packages, misc=misc)
        return d

def buildVersions():
    java6_lucid = 'echo "deb http://ppa.launchpad.net/webupd8team/java/ubuntu lucid main" >> /etc/apt/sources.list.d/webupd8.list && apt-key adv --keyserver keyserver.ubuntu.com --recv-keys EEA14886 &&  echo oracle-java6-installer shared/accepted-oracle-license-v1-1 select true | debconf-set-selections && apt-get update && apt-get -y install oracle-java6-installer oracle-java6-set-default'
    java6_precise = 'echo "deb http://ppa.launchpad.net/webupd8team/java/ubuntu precise main" >> /etc/apt/sources.list.d/webupd8.list && apt-key adv --keyserver keyserver.ubuntu.com --recv-keys EEA14886 &&  echo oracle-java6-installer shared/accepted-oracle-license-v1-1 select true | debconf-set-selections && apt-get update && apt-get -y install oracle-java6-installer oracle-java6-set-default'
    java6_trusty = 'echo "deb http://ppa.launchpad.net/webupd8team/java/ubuntu trusty main" >> /etc/apt/sources.list.d/webupd8.list && apt-key adv --keyserver keyserver.ubuntu.com --recv-keys EEA14886 &&  echo oracle-java6-installer shared/accepted-oracle-license-v1-1 select true | debconf-set-selections && apt-get update && apt-get -y install oracle-java6-installer oracle-java6-set-default'
    java7 = 'apt-get install -y openjdk-7-jdk'

    v = {}
    v['4.0'] = Dockerfile('4.0', 'ubuntu:10.04', 'bc bison bsdmainutils build-essential curl flex g++-multilib gcc-multilib git gnupg gperf lib32ncurses5-dev lib32readline-gplv2-dev lib32z1-dev libesd0-dev libncurses5-dev libsdl1.2-dev libwxgtk2.8-dev libxml2-utils lzop pngcrush schedtool xsltproc zip zlib1g-dev', java6_lucid)
    v['4.1'] = Dockerfile('4.4', 'ubuntu:12.04', 'bc bison bsdmainutils build-essential curl flex g++-multilib gcc-multilib git gnupg gperf lib32ncurses5-dev lib32readline-gplv2-dev lib32z1-dev libesd0-dev libncurses5-dev libsdl1.2-dev libwxgtk2.8-dev libxml2-utils lzop pngcrush schedtool xsltproc zip zlib1g-dev', java6_precise)
    v['4.4'] = Dockerfile('4.4', 'ubuntu:14.04', 'bc bison bsdmainutils build-essential curl flex g++-multilib gcc-multilib git gnupg gperf lib32ncurses5-dev lib32readline-gplv2-dev lib32z1-dev libesd0-dev libncurses5-dev libsdl1.2-dev libwxgtk2.8-dev libxml2-utils lzop pngcrush schedtool xsltproc zip zlib1g-dev', java6_trusty)
    v['5.0'] = Dockerfile('5.0', 'ubuntu:14.04', 'bc bison bsdmainutils build-essential curl flex g++-multilib gcc-multilib git gnupg gperf lib32ncurses5-dev lib32readline-gplv2-dev lib32z1-dev libesd0-dev libncurses5-dev libsdl1.2-dev libwxgtk2.8-dev libxml2-utils lzop pngcrush schedtool xsltproc zip zlib1g-dev', java7)
    return v

class AospDocker:
    def __init__(self):
        self.versions = buildVersions()

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
        id = subprocess.check_output('docker run -td -v "$PWD:/aosp" {name} /bin/bash'.format(name=dockerfile.getImageName()), shell=True).strip()
        subprocess.call('docker exec -it {id} /bin/bash -ic "cd /aosp && declare -p | sed -e \'/declare -[a-z]*r/d\' > /env.bash && declare -f >> /env.bash"'.format(id=id), shell=True)
        self.config.set('main', 'container-id', id)
        print 'done: {id}'.format(id=id)
        print 'You can now use aosp exec [COMMAND]'

        pass

    def execute(self):
        s, id = self.getContainer()

        if len(sys.argv) == 2:
            print 'Not enough parameters.'
            print 'Usage: aosp exec [COMMAND...]'
            return

        cmd = " ".join(sys.argv[2:])

        subprocess.call('docker exec -it {id} /bin/bash -ic "source /env.bash && cd \$PWD && {cmd} && declare -p | sed -e \'/declare -[a-z]*r/d\' > /env.bash && declare -f >> /env.bash"'.format(id=id, cmd=cmd), shell=True)

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