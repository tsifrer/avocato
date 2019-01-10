*************
API Reference
*************

Serializers
===========

.. currentmodule:: avocato

.. autoclass:: Serializer
   :members:
   :exclude-members: to_value,default_getter

.. autoclass:: DictSerializer
   :members:
   :exclude-members: default_getter


Fields
======

.. autoclass:: Field

.. autoclass:: StrField

.. autoclass:: EmailField

.. autoclass:: IntField

.. autoclass:: FloatField

.. autoclass:: BoolField

.. autoclass:: DecimalField

.. autoclass:: DateTimeField

.. autoclass:: DictField

.. autoclass:: MethodField


Validators
==========

.. autoclass:: Validator

.. autoclass:: Required

.. autoclass:: Email

.. autoclass:: Length

.. autoclass:: OneOf

.. autoclass:: OneOfType


Exceptions
==========

.. autoclass:: AvocatoError

.. autoclass:: AvocatoValidationError
