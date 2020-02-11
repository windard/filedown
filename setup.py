# coding=utf-8

from setuptools import setup

version = '0.2.3'

entry_points = {
    'console_scripts': [
        'filedown=filedown.filedown:main',
        'only_download=filedown.only_download:main'
    ],
}

setup(
    name='filedown',
    packages=['filedown'],
    version=version,
    description='filedown = Multi Thread to Download',
    author='Windard Yang',
    author_email='windard@qq.com',
    url='https://github.com/windard/filedown',
    install_requires=[
        'Click',
        'tqdm',
        'requests',
        'gevent',
    ],
    license="MIT",
    entry_points=entry_points,
)
