import sys


class Platforms:
    Linux = 1
    Mac = 2
    Windows = 3


def platform(force_test_string=None):
    if force_test_string:
        platform_string = force_test_string
    else:
        platform_string = sys.platform  # pragma: no cover

    if "linux" in platform_string:
        return Platforms.Linux
    elif "darwin" in platform_string:
        return Platforms.Mac
    elif "win" in platform_string:
        return Platforms.Windows
    else:
        raise Exception('Unsupported OS!, Platform string = \"%s\"' % platform_string)


def exe_extension(force_test_platform=None):
    if force_test_platform:
        this_platform = force_test_platform
    else:
        this_platform = platform()  # pragma: no cover

    _exe_extension = ''
    if this_platform == Platforms.Windows:
        _exe_extension = '.exe'
    return _exe_extension
