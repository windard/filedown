# coding=utf-8

import setuptools
from setuptools import setup

version = '0.6.1'

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()


entry_points = {
    'console_scripts': [
        'filedown=filedown.filedown:main',
        'concurrent_download=filedown.concurrent_download:main'
    ],
}

setup(
    name='filedown',
    version=version,
    author='Windard Yang',
    author_email='windard@qq.com',
    description='filedown: Multi Thread Downloader',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/windard/filedown',
    packages=setuptools.find_packages(),
    install_requires=[
        'Click',
        'tqdm',
        'requests',
    ],
    license="MIT",
    entry_points=entry_points,
    classifiers=[
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
