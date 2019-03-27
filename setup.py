# coding=utf-8

from setuptools import setup

version = '0.1.2'

entry_points = {
    'console_scripts': [
        'filedown=filedown.filedown:main',
    ],
}

setup(
    name='filedown',
    packages=['filedown'],
    version=version,
    description='filedown = Multi Thread to Download',
    author='Windard Yang',
    author_email='windard@qq.com',
    url='https://windard.com',
    install_requires=[
        'Click',
        'tqdm',
        'requests',
    ],
    license="MIT",
    entry_points=entry_points,
)
