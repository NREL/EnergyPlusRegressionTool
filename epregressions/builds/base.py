class KnownBuildTypes:
    Makefile = "makefile"
    VisualStudio = "visual_studio"
    Installation = "install"


class BaseBuildDirectoryStructure:
    def __init__(self):
        self.build_directory = None
        self.run = None

    def set_run_flag(self, run_this_directory):
        self.run = run_this_directory

    def get_build_tree(self):
        raise NotImplementedError('Must implement get_build_tree in derived classes')
