from setuptools import setup

import codecs
import os
import re
import versioneer


setup(
    name="chimedb.node",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    packages=["chimedb.node"],
    zip_safe=False,
    install_requires=[
        "chimedb @ git+ssh://git@github.com/chime-experiment/chimedb.git",
        "peewee > 3",
        "future",
    ],
    author="CHIME collaboration",
    author_email="dvw@phas.ubc.ca",
    description="CHIME GPU node hardware database",
    license="GPL v3.0",
    url="https://github.org/chime-experiment/chimedb_node",
)
