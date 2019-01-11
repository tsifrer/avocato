*********************************************
avocato: simple and fast object serialization
*********************************************

.. container:: badges

    .. image:: https://travis-ci.org/tsifrer/avocato.svg?branch=master
        :target: https://travis-ci.org/tsifrer/avocato?branch=master
        :alt: Travis-CI

    .. image:: https://readthedocs.org/projects/avocato/badge/?version=latest
        :target: https://avocato.rtfd.io
        :alt: Documentation Status

    .. image:: https://codecov.io/gh/tsifrer/avocato/branch/master/graph/badge.svg
        :target: https://codecov.io/gh/tsifrer/avocato
        :alt: Code Coverage


**avocato** is a simple and fast ORM/framework-agnostic object serialization library for
converting complex objects to and from simple Python datatypes.

Don't be scared if you're using an ORM/framework. It can easily be adapted to be used with any
ORM/framework of your liking. Currently it supports Django ORM and peewee.

This library is heavily influenced by `serpy`_.

Installation
============

.. code-block:: bash

    $ pip install avocato

Documentation
=============

Find documentation at `avocato.rtfd.io`_

Example
=======

.. code-block:: python

    import avocato

    class Bar(object):
        patrick = 'star'


    class Foo(object):
        over = 9000
        spongebob = 'squarepants'
        bar = Bar()


    class BarSerializer(avocato.Serializer):
        patrick = avocato.StrField()


    class FooSerializer(avocato.Serializer):
        over = avocato.IntField()
        spongebob = avocato.StrField()
        bar = BarSerializer()


    foo = Foo()
    FooSerializer(foo).data
    # {'over': 9000, 'spongebob': 'squarepants', 'bar': {'patrick': 'star'}}


.. _serpy: https://github.com/clarkduvall/serpy
.. _avocato.rtfd.io: https://avocato.rtfd.io