import docker

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
        self.client = docker.Client(base_url='unix://var/run/docker.sock')

    def getImages(self):
        imageInfos = self.client.images()
        images = []
        for info in imageInfos:
            images.append(Image(info))
        return images

    def removeImage(self, id):
        return self.client.remove_image(image=id)

    def getContainers(self):
        containerInfos = self.client.containers(all=True)
        containers = []
        for info in containerInfos:
            containers.append(Container(info))
        return containers

    def removeContainer(self, id):
        return self.client.remove_container(container=id, force=True)

    def startContainer(self, id):
        return self.client.start(container=container['Id'])