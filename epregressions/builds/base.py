class KnownBuildTypes:
    Makefile = "makefile"
    VisualStudio = "visual_studio"
    Installation = "install"


class BaseBuildDirectoryStructure(object):
    def __init__(self):
        self.build_directory = None
        self.run = None

    def set_build_directory(self, build_directory):
        raise NotImplementedError('Must implement set_build_directory(str) in derived classes')

    def verify(self):
        raise NotImplementedError('Must implement verify() in derived classes')

    def get_build_tree(self):
        raise NotImplementedError('Must implement get_build_tree() in derived classes')
