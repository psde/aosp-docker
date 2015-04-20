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

import docker
import subprocess
import os
from dockerfile import Dockerfile


class Container():
    def __init__(self, info):
        self.id = info['Id']
        self.image = info['Image']
        self.names = info['Names']
        self.created = info['Created']
        self.up = False if info['Status'].lower().startswith('exited') else True
        self.status = info['Status']

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        attrs = ', '.join("%s: %s" % item for item in vars(self).items())
        return '<{attrs}>'.format(attrs=attrs)


class Image():
    def __init__(self, info):
        self.id = info['Id']
        self.parent = info['ParentId']
        self.created = info['Created']
        self.repo = info['RepoTags'][0]
        self.repoTags = info['RepoTags']

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        attrs = ', '.join("%s: %s" % item for item in vars(self).items())
        return '<{attrs}>'.format(attrs=attrs)


class Client():
    def __init__(self):
        self.client = docker.Client(**docker.utils.kwargs_from_env())

    def getImages(self):
        imageInfos = self.client.images()
        images = []
        for info in imageInfos:
            images.append(Image(info))
        return images

    def removeImage(self, id):
        return self.client.remove_image(image=id)

    def buildImage(self, dockerfile):
        if isinstance(dockerfile, Dockerfile) == False:
            raise TypeError('{cls} is not derrived from Dockerfile'.format(cls=dockerfile))

        cmd = 'docker build -t {name} -'.format(name=dockerfile.getImageName())
        p = subprocess.Popen(cmd.split(" "), stdin=subprocess.PIPE, stderr=subprocess.STDOUT)
        p.communicate(input=b'' + dockerfile.buildDockerfile())[0]

    def getContainers(self):
        containerInfos = self.client.containers(all=True)
        containers = []
        for info in containerInfos:
            containers.append(Container(info))
        return containers

    def getContainerById(self, id):
        containers = self.getContainers()
        try:
            return filter(lambda container: container.id == id, containers)[0]
        except Exception:
            return None

    def removeContainer(self, id):
        return self.client.remove_container(container=id, force=True)

    def createContainer(self, dockerfile, command, environment, volumes):
        if isinstance(dockerfile, Dockerfile) == False:
            raise TypeError('{cls} is not derrived from Dockerfile'.format(cls=dockerfile))

        container_volumes = []
        binds = {}
        for key, value in volumes.iteritems():
            binds[key] = {'bind': value, 'ro': False}
            container_volumes.append(value)

        container = self.client.create_container(tty=True, detach=True, image=dockerfile.getImageName(), command=command, volumes=container_volumes, environment=environment)
        self.client.start(privileged=True, network_mode='host', container=container['Id'], binds=binds)
        return self.getContainerById(container['Id'])

    def interactive(self, id, command):
        # docker-py has now way to execute a command interactively
        subprocess.call('docker exec -it {id} {command}'.format(id=id, command=command), shell=True)

    def startContainer(self, id):
        return self.client.start(container=id)
