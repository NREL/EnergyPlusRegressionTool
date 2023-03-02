import unittest

from energyplus_regressions.ep_platform import platform, exe_extension, Platforms


class TestCrossPlatform(unittest.TestCase):

    def test_supported_platforms(self):
        self.assertEqual(Platforms.Linux, platform(force_test_string='linux2'))
        self.assertEqual(Platforms.Windows, platform(force_test_string='win32'))
        self.assertEqual(Platforms.Mac, platform(force_test_string='darwin'))

    def test_unsupported_platform(self):
        with self.assertRaises(Exception):
            platform('riscos')


class TestExeExtension(unittest.TestCase):

    def test_non_windows(self):
        self.assertEqual('', exe_extension(force_test_platform=Platforms.Linux))
        self.assertEqual('', exe_extension(force_test_platform=Platforms.Mac))

    def test_windows(self):
        self.assertEqual('.exe', exe_extension(force_test_platform=Platforms.Windows))
