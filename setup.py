import codecs
import os
from setuptools import setup, find_packages

from epregressions import VERSION

this_dir = os.path.abspath(os.path.dirname(__file__))
with codecs.open(os.path.join(this_dir, 'README.md'), encoding='utf-8') as i_file:
    long_description = i_file.read()

setup(
    name='energyplus_regressions',
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
    include_package_data=True,
    install_requires=['PyPubSub==4.0.3', 'beautifulsoup4==4.9.3'],
    entry_points={
        'console_scripts': [
            'eplus_regression_runner=epregressions.runner:main_gui',
        ],
    },
    python_requires='>=3.5',
)
