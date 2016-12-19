# -*- coding: utf-8 -*-
from distutils.core import setup
from setuptools import find_packages

setup(
    name='pyawscli',
    version='0.1.0',
    author=u'Chris Pagnutti',
    author_email='chris.pagnutti@gmail.com',
    packages=find_packages(),
    url='https://bitbucket.org/Pacopag/pyawscli',
    license='MIT',
    description='Python wrapper for aws-cli',
    long_description='Python wrapper for aws-cli',
    zip_safe=False,
)