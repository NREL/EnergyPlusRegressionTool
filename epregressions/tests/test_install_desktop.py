import unittest

from epregressions.install_desktop import main


class TestInstallFunction(unittest.TestCase):

    def test_install_script(self):
        resulting_file = main(test_mode=True)
        with open(resulting_file) as f_result:
            lines = f_result.readlines()
            for i, row in enumerate(lines):
                self.assertNotIn('{', row)
                self.assertNotIn('}', row)
                if i == 0:
                    self.assertIn('[Desktop Entry]', row)
                else:
                    self.assertIn('=', row)
