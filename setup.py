import re
from codecs import open

import setuptools


with open('avocato/__init__.py', 'r') as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1)

if not version:
    raise RuntimeError('Cannot find version information')

packages = setuptools.find_packages(exclude=[
    'tests*',
    'benchmarks*',
    'docs*',
])

setuptools.setup(
    name='avocato',
    version=version,
    description='',
    author='Tomaz Sifrer',
    author_email='tomazz.sifrer@gmail.com',
    url='https://github.com/tsifrer/avocato',
    packages=packages,
    license='MIT',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Internet',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords=('serialization', 'deserialization', 'validation', 'rest', 'json', 'api', 'fast'),
)
