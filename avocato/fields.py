from datetime import datetime
from decimal import Decimal

from . import validators as avocato_validators


class Field(object):
    """:class:`Field` handles converting between primitive values and internal datatypes. It also
    deals with validating input values.

    :param str attr: The attribute to get on the object. If this is not supplied, the name this
        field was assigned to on the serializer will be used.
    :param str label: A label to use as the name of the serialized field instead of using the
        attribute name of the field.
    :param bool required: Whether the field is required.
    :param list validators: List of validators to run when calling ``.is_valid()`` method on the
        serializer.
    :param bool call: Whether the value should be called after it is retrieved
        from the object. Useful if an object has a method to be serialized.
    :param bool is_create_field: Whether the field is used to populate the instance when creating
        a new object via ``to_instance`` method on the serializer.
    :param bool call: Whether the field is used to populate the instance when updating an object
        via ``to_instance`` method on the serializer.
    """
    getter_takes_serializer = False
    accepted_types = None

    def __init__(
        self,
        attr=None,
        label=None,
        required=True,
        validators=None,
        call=False,
        is_create_field=True,
        is_update_field=True,
    ):
        self.attr = attr
        self.label = label
        self.required = required
        self.call = call
        self.is_create_field = is_create_field
        self.is_update_field = is_update_field
        self.validators = validators or []

        if required:
            self.validators.insert(0, avocato_validators.Required())
            if self.accepted_types:
                self.validators.insert(1, avocato_validators.OneOfType(choices=self.accepted_types))

    def to_value(self, value):
        """Transform the serialized value.

        Override this method to clean and validate values serialized by this field.
        """
        return value

    def as_getter(self, serializer_field_name, serializer_cls):
        """Returns a function that fetches an attribute from an object.
        Return `None` to use the default getter for the serializer defined in
        `Serializer.default_getter`.
        If a `Field` has `getter_takes_serializer = True`, then the getter returned from this method
        will be called with the `Serializer` instance as the first argument, and the object being
        serialized as the second.
        """
        return None


class StrField(Field):
    """Converts input value to string.

    :param int max_length: Maximum lenght of the string. If present, adds a validator for max lenght
        which will be run when ``is_valid`` method on the serializer is called.
    :param int min_length: Minimum lenght of the string. If present, adds a validator for min lenght
        which will be run when ``is_valid`` method on the serializer is called.
    :param list choices: Available choices. If present, adds a validator that checks if value is
        present in choices and will be run when ``is_valid`` method on the serializer is called.
    """
    accepted_types = (str,)
    to_value = staticmethod(str)

    def __init__(self, **kwargs):
        self.max_length = kwargs.pop('max_length', None)
        self.min_length = kwargs.pop('min_length', None)
        self.choices = kwargs.pop('choices', None)
        super().__init__(**kwargs)

        if self.max_length is not None:
            self.validators.append(
                avocato_validators.Length(max_length=self.max_length)
            )
        if self.min_length is not None:
            self.validators.append(
                avocato_validators.Length(min_length=self.min_length)
            )

        if self.choices is not None:
            self.validators.append(
                avocato_validators.OneOf(choices=self.choices)
            )


class EmailField(StrField):
    """Converts input value to email.
    """
    accepted_types = (str,)
    to_value = staticmethod(str)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.validators.append(avocato_validators.Email())


class IntField(Field):
    """Converts input value to integer.
    """
    accepted_types = (int,)
    to_value = staticmethod(int)


class FloatField(Field):
    """Converts input value to float.
    """
    accepted_types = (float,)
    to_value = staticmethod(float)


class BoolField(Field):
    """Converts input value to bool.
    """
    accepted_types = (bool,)
    to_value = staticmethod(bool)


class DecimalField(Field):
    """Converts input value to string, so it accurately shows decimal numbers.
    """
    accepted_types = (Decimal,)

    @staticmethod
    def to_value(value):
        if value is None:
            return None
        return str(value)


class DateTimeField(Field):
    """Converts input value to ISO format date.
    """
    accepted_types = (datetime,)

    @staticmethod
    def to_value(value):
        if value is None:
            return None
        return value.isoformat()


class DictField(Field):
    """Converts input value to dict.
    """
    accepted_types = (dict,)
    to_value = staticmethod(dict)


class MethodField(Field):
    """Calls a method on the :class:`Serializer` to get the value.
    """
    getter_takes_serializer = True

    def __init__(self, method=None, **kwargs):
        super(MethodField, self).__init__(**kwargs)
        self.method = method

    def as_getter(self, serializer_field_name, serializer_cls):
        method_name = self.method
        if method_name is None:
            method_name = 'get_{0}'.format(serializer_field_name)
        return getattr(serializer_cls, method_name)
