import codecs
import os
from platform import system
from setuptools import setup, find_packages

from energyplus_regressions import NAME, VERSION

this_dir = os.path.abspath(os.path.dirname(__file__))
with codecs.open(os.path.join(this_dir, 'README.md'), encoding='utf-8') as i_file:
    long_description = i_file.read()


install_requires = ['PyPubSub', 'beautifulsoup4', 'PLAN-Tools==0.5']
if system() == 'Windows':
    install_requires.append('pypiwin32')

setup(
    name=NAME,
    version=VERSION,
    packages=find_packages(exclude=['test', 'tests', 'test.*']),
    url='https://github.com/NREL/EnergyPlusRegressionTool',
    license='',
    author='Edwin Lee',
    author_email='',
    description='A Python 3 library for evaluating regressions between EnergyPlus builds.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    test_suite='nose.collector',
    tests_require=['nose'],
    keywords='energyplus',
    include_package_data=True,  # use /MANIFEST.in file for declaring package data
    install_requires=install_requires,
    entry_points={
        'gui_scripts': [
            'energyplus_regression_runner=energyplus_regressions.runner:main_gui',
        ],
        'console_scripts': [
            'energyplus_regression_configure=energyplus_regressions.configure:configure_cli',
        ],
    },
    python_requires='>=3.5',
)
