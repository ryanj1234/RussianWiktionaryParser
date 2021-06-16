# -*- coding: utf-8 -*-

# Learn more: https://github.com/kennethreitz/setup.py

from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='russianwiktionaryparser',
    version='0.1.0',
    description='Russian Wiktionary Parser',
    long_description=readme,
    author='Ryan Harmon',
    author_email='ryanjharmon1@gmail.com',
    url='https://github.com/ryanj1234/RussianWiktionaryParser',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)