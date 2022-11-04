#!/usr/bin/env python3

from setuptools import setup
with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()

setup(
    name='capice-resources',
    version='1.0.0.dev0',
    packages=[],
    url='https://capice.molgeniscloud.org/',
    license='LGPL-3.0',
    author='Molgenis',
    author_email='molgenis-support@umcg.nl',
    description='Resource files for CAPICE to train new CAPICE models',
    long_description=long_description,
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: LGPL-3.0',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10'
    ],
    python_requires='>=3.9.*',
    install_requires=[
        'pandas==1.3.4',
        'numpy==1.22.0',
        'matplotlib==3.5.1',
        'scikit-learn==1.0.2',
        'graphviz==0.19.1'
    ],
    extras_require={
        'test': [
            'pytest',
        ]
    }
)
