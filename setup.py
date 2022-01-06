import glob
import os
import sys
from distutils.core import setup
from typing import List


def get_version(filename):
    import ast
    version = None
    with open(filename) as f:
        for line in f:
            if line.startswith('__version__'):
                version = ast.parse(line).body[0].value.s
                break
        else:
            raise ValueError('No version found in %r.' % filename)
    if version is None:
        raise ValueError(filename)
    return version


if sys.version_info < (3, 6):
    msg = 'aavm works with Python 3.6 and later.\nDetected %s.' % str(sys.version)
    sys.exit(msg)

lib_version = get_version(filename='include/aavm/__init__.py')

setup(
    name='aavm',
    packages=[
        'aavm',
        'aavm.cli',
        'aavm.cli.commands'
        'aavm.utils'
    ],
    package_dir={
        'aavm': 'include/aavm'
    },
    package_data={
        "aavm": [
            "schemas/*/*.json",
        ],
    },
    version=lib_version,
    license='MIT',
    description='AAVM - Almost A Virtual Machine - Docker Containers that want to be Virtual Machines',
    author='Andrea F. Daniele',
    author_email='afdaniele@ttic.edu',
    url='https://github.com/afdaniele/aavm',
    download_url='https://github.com/afdaniele/aavm/tarball/{}'.format(lib_version),
    zip_safe=False,
    include_package_data=True,
    keywords=['code', 'container', 'containerization', 'package', 'toolkit', 'docker'],
    install_requires=[
        'docker>=4.4.0',
        'requests',
        'jsonschema',
        'termcolor',
        'pyyaml',
        'sshconf',
        'cryptography',
        'terminaltables',
        'x-docker>=0.0.2',
        *(['dataclasses'] if sys.version_info < (3, 7) else [])
    ],
    scripts=[
        'include/aavm/bin/aavm'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
)
