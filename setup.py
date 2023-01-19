#!/usr/bin/env python3

from setuptools import setup, find_namespace_packages
with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()

setup(
    name='capice-resources',
    version='5.0.0',
    packages=find_namespace_packages('src', exclude=['tests']),
    package_dir={"": "src"},
    url='https://capice.molgeniscloud.org/',
    license='LGPL-3.0',
    author='Molgenis',
    author_email='molgenis-support@umcg.nl',
    description='Resource files for CAPICE to train new CAPICE models',
    long_description=long_description,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: LGPL-3.0',
        'Programming Language :: Python :: 3.10'
    ],
    python_requires='>=3.10.*',
    install_requires=[
        'pandas==1.5.2',
        'numpy==1.24.1',
        'matplotlib==3.5.1',
        'scikit-learn==1.0.2',
        'graphviz==0.19.1',
        'seaborn==0.12.1',
    ],
    extras_require={
        'test': [
            'pytest',  # pytest
            'coverage',  # coverage run -m pytest --junitxml=results.xml && coverage html
            'mypy',  # mypy --ignore-missing-imports src/
            'flake8',  # flake8 src/ tests/
            'flake8-import-order'
        ]
    },
    entry_points={
        'console_scripts': [
            'process-vep = molgenis.capice_resources.process_vep.__main__:main',
            'compare-model-features = '
            'molgenis.capice_resources.compare_model_features.__main__:main',
            'compare-model-performance = '
            'molgenis.capice_resources.compare_model_performance.__main__:main',
            'threshold-calculator = molgenis.capice_resources.threshold_calculator.__main__:main',
            'train-data-creator = molgenis.capice_resources.train_data_creator.__main__:main',
            'balance-dataset = molgenis.capice_resources.balance_dataset.__main__:main'
        ]
    }
)
