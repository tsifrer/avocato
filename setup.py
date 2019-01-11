import re
from codecs import open

import setuptools


with open('avocato/__init__.py', 'r') as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1)
if not version:
    raise RuntimeError('Cannot find version information')

with open('README.rst', 'r') as f:
    readme = f.read()

setuptools.setup(
    name='avocato',
    version=version,
    description='Simple and fast object serialization.',
    long_description=readme,
    long_description_content_type='text/x-rst',
    author='Tomaz Sifrer',
    author_email='tomazz.sifrer@gmail.com',
    url='https://github.com/tsifrer/avocato',
    packages=['avocato'],
    license='MIT',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy'
    ],
    keywords=('serialization', 'deserialization', 'validation', 'rest', 'json', 'api', 'fast'),
    extras_require={
        'peewee': ['peewee>=3.8.1', 'psycopg2-binary>=2.7.6.1'],
        'django': ['django>=2.1.5', 'psycopg2-binary>=2.7.6.1'],
    },
)
