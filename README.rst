*********************************************
avocato: simple and fast object serialization
*********************************************

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

Serializer Example
==================

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