#!/usr/bin/env python

# Landsat Util
# License: CC0 1.0 Universal

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from landsat import __version__


def readme():
    with open('README.rst') as f:
        return f.read()

test_requirements = [
  'nose==1.3.3'
]

setup(
    name='landsat-util',
    version=__version__,
    description='A utility to search, download and process Landsat 8' +
    ' satellite imagery',
    long_description=readme(),
    author='Development Seed',
    author_email='info@developmentseed.org',
    scripts=['bin/landsat'],
    url='https://github.com/developmentseed/landsat-util',
    packages=['landsat'],
    include_package_data=True,
    license='CCO',
    platforms='Posix; MacOS X; Windows',
    install_requires=[
      'requests==2.5.3',
      'python-dateutil==2.2',
      'numpy==1.9.1',
      'termcolor==1.1.0',
      'rasterio==0.18',
      'six==1.9.0',
      'scipy==0.15.1',
      'scikit-image==0.10.1',
      'homura==0.1.0'
    ],
    test_suite='nose.collector',
    test_require=test_requirements
)
