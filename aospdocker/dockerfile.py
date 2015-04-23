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


class Dockerfile():
    def __init__(self, version, base, packages, java, misc=''):
        self.version = version
        self.base = base
        self.packages = packages
        self.java = java
        self.misc = misc

    def get_image_name(self):
        return 'aosp-docker-{version}'.format(version=self.version)

    def build_dockerfile(self):
        misc = ''
        if self.misc != '':
            misc = "RUN {cmd}".format(cmd=self.misc)
        d = ("FROM {base}\n"
             "MAINTAINER Mathias Garbe <mathias.garbe@inovex.de>\n"
             "RUN touch /env.bash && echo 'source /env.bash' > /rc.bash && echo 'cd $PWD' >> /rc.bash && echo \"trap \\\"declare -p | sed -e '/declare -[a-z]*r/d' > /env.bash && declare -f >> /env.bash\\\" EXIT\" >> /rc.bash\n"
             "RUN chmod 777 /env.bash && chmod 777 /rc.bash\n"
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
             "RUN apt-get clean && rm -rf /var/tmp/*\n").format(base=self.base, java=self.java, packages=self.packages, misc=misc)
        return d

    @staticmethod
    def build_versions():
        java6_lucid = 'apt-get install -y python-software-properties && add-apt-repository ppa:sun-java-community-team/sun-java6 && apt-get update && echo sun-java6-jdk shared/accepted-sun-dlj-v1-1 select true | /usr/bin/debconf-set-selections && apt-get install -y sun-java6-jdk'
        java6_precise = 'echo "deb http://ppa.launchpad.net/webupd8team/java/ubuntu precise main" >> /etc/apt/sources.list.d/webupd8.list && apt-key adv --keyserver keyserver.ubuntu.com --recv-keys EEA14886 &&  echo oracle-java6-installer shared/accepted-oracle-license-v1-1 select true | debconf-set-selections && apt-get update && apt-get -y install oracle-java6-installer oracle-java6-set-default'
        java6_trusty = 'echo "deb http://ppa.launchpad.net/webupd8team/java/ubuntu trusty main" >> /etc/apt/sources.list.d/webupd8.list && apt-key adv --keyserver keyserver.ubuntu.com --recv-keys EEA14886 &&  echo oracle-java6-installer shared/accepted-oracle-license-v1-1 select true | debconf-set-selections && apt-get update && apt-get -y install oracle-java6-installer oracle-java6-set-default'
        java7 = 'apt-get install -y openjdk-7-jdk'

        misc_git = 'apt-get install -y python-software-properties && add-apt-repository ppa:git-core/ppa && apt-get update && apt-get install -y git'

        v = {}
        v['4.0'] = Dockerfile('4.0', 'ubuntu:10.04', 'bash-completion uboot-mkimage gnupg flex bison gperf build-essential zip curl zlib1g-dev libc6-dev lib32ncurses5-dev ia32-libs x11proto-core-dev libx11-dev lib32readline5-dev lib32z-dev libgl1-mesa-dev g++-multilib mingw32 tofrodos python-markdown libxml2-utils xsltproc', java6_lucid, misc_git)
        v['4.1'] = Dockerfile('4.1', 'ubuntu:12.04', 'bash-completion uboot-mkimage bc bison bsdmainutils build-essential curl flex g++-multilib gcc-multilib git gnupg gperf lib32ncurses5-dev lib32readline-gplv2-dev lib32z1-dev libesd0-dev libncurses5-dev libsdl1.2-dev libwxgtk2.8-dev libxml2-utils lzop pngcrush schedtool xsltproc zip zlib1g-dev', java6_precise)
        v['4.2'] = v['4.1']
        v['4.3'] = v['4.2']
        v['4.4'] = Dockerfile('4.4', 'ubuntu:14.04', 'bash-completion u-boot-tools bc bison bsdmainutils build-essential curl flex g++-multilib gcc-multilib git gnupg gperf lib32ncurses5-dev lib32readline-gplv2-dev lib32z1-dev libesd0-dev libncurses5-dev libsdl1.2-dev libwxgtk2.8-dev libxml2-utils lzop pngcrush schedtool xsltproc zip zlib1g-dev', java6_trusty)
        v['5.0'] = Dockerfile('5.0', 'ubuntu:14.04', 'bash-completion u-boot-tools bc bison bsdmainutils build-essential curl flex g++-multilib gcc-multilib git gnupg gperf lib32ncurses5-dev lib32readline-gplv2-dev lib32z1-dev libesd0-dev libncurses5-dev libsdl1.2-dev libwxgtk2.8-dev libxml2-utils lzop pngcrush schedtool xsltproc zip zlib1g-dev', java7)
        return v
