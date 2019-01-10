import operator
from collections import Iterable, defaultdict

from .exceptions import AvocatoError, AvocatoValidationError
from .fields import Field


def _compile_fields(field, name, serializer_cls):
    getter = field.as_getter(name, serializer_cls)
    if getter is None:
        getter = serializer_cls.default_getter(field.attr or name)

    # Set the field name to a supplied label; defaults to the attribute name.
    field._name = field.label or name
    field._getter = getter
    return field


class SerializerMeta(type):

    @staticmethod
    def _get_fields_from_base_classes(serializer_cls):
        fields = []
        # Get all the fields from base classes.
        for cls in serializer_cls.__mro__[::-1]:
            if isinstance(cls, SerializerMeta):
                fields += cls.fields
        return fields

    @staticmethod
    def _compile_fields(field_map, serializer_cls):
        return [
            _compile_fields(field, name, serializer_cls)
            for name, field in field_map.items()
        ]

    @staticmethod
    def parse_meta_class(cls, meta_cls, direct_fields):
        return None, None, None

    def __new__(cls, name, bases, attrs):
        # Fields declared directly on the class.
        direct_fields = {}
        meta_fields = {}
        # Take all the Fields from the attributes.
        for attr_name, field in attrs.items():
            if isinstance(field, Field):
                direct_fields[attr_name] = field
        for k in direct_fields.keys():
            del attrs[k]

        meta_model = None
        if 'Meta' in attrs:
            meta_model, field_names, meta_fields = cls.parse_meta_class(
                cls, attrs['Meta'], direct_fields
            )
            del attrs['Meta']

            for direct_field in direct_fields:
                missing_fields = []
                if direct_field not in field_names:
                    missing_fields.append(direct_field)

                if missing_fields:
                    raise AvocatoError(
                        'Fields {} are missing in Meta class'.format(missing_fields)
                    )

        meta_fields.update(direct_fields)

        real_cls = super(SerializerMeta, cls).__new__(cls, name, bases, attrs)
        compiled_fields = cls._compile_fields(meta_fields, real_cls)

        base_classes_fields = cls._get_fields_from_base_classes(real_cls)

        real_cls._meta_model = meta_model
        all_fields = compiled_fields + base_classes_fields
        real_cls.fields = all_fields
        real_cls.create_fields = [field for field in all_fields if field.is_create_field]
        real_cls.update_fields = [field for field in all_fields if field.is_update_field]
        return real_cls


class Serializer(Field, metaclass=SerializerMeta):
    """Base class for custom object serializers.

    ``Serializer`` can be used as a Field to create nested schemas. A serializer is defined by
    subclassing Serializer and adding each Field as a class variable:

    Example:

    .. code-block:: python

        class MyObject(object):
            bar = 2
            baz = 'hello'

        class FooSerializer(Serializer):
            bar = IntField()
            baz = StrField()

        obj = MyObject()
        FooSerializer(obj).data
        # {'bar': 2, 'baz': 'hello'}
    """
    fields = []
    create_fields = []
    update_fields = []
    _validation_successful = False

    #: The default getter used if :meth:`Field.as_getter` returns None.
    default_getter = operator.attrgetter

    def __init__(self, instance=None, many=False, data=None, **kwargs):
        super(Serializer, self).__init__(**kwargs)
        self.instance = instance
        self.many = many
        self._initial_data = data
        self._serialized_data = None
        self.errors = {}

    def _serialize(self, instance, fields):
        v = {}
        for field in fields:
            if field.getter_takes_serializer:
                result = field._getter(self, instance)
            else:
                try:
                    result = field._getter(instance)
                    if field.call:
                        result = result()
                except (KeyError, AttributeError):
                    if field.required:
                        raise AvocatoError('Field {} is required'.format(field._name))
                    else:
                        continue

                if field.required and result is None:
                    raise AvocatoError(
                        "Field {} is required, but it's value is None".format(field._name)
                    )

                if result is not None:
                    result = field.to_value(result)
            v[field._name] = result
        return v

    def to_value(self, instance):
        if self.many:
            if not instance or not isinstance(instance, Iterable):
                return []
            serialize = self._serialize
            return [serialize(o, self.fields) for o in instance]
        return self._serialize(instance, self.fields)

    @property
    def data(self):
        """Get the serialized data from the :class:`Serializer`.

        The data will be cached for future accesses.
        """
        if self._serialized_data is None:
            self._serialized_data = self.to_value(self.instance)
        return self._serialized_data

    def validate(self, data):
        pass

    def _validate(self, data):
        if self.instance:
            fields = self.update_fields
        else:
            fields = self.create_fields

        errors = defaultdict(list)
        for field in fields:
            if not field.required and field._name not in data:
                continue

            # Loop trough all validators on field and executed them
            if field.validators:
                for validator in field.validators:
                    try:
                        validator(data.get(field._name))
                    except AvocatoValidationError as e:
                        errors[field._name] += e.messages
                        break  # TODO: this makes it so it' always has only one error before the
                        # custom validate_func. Maybe think of how to handle errors. Just one
                        # by one, or multiple at once?

            # Call validate_<field> if it exist to get field specific errors
            try:
                validate_func = getattr(self, 'validate_{0}'.format(field._name))
            except AttributeError:
                pass
            else:
                try:
                    validate_func(data.get(field._name))
                except AvocatoValidationError as e:
                    errors[field._name] += e.messages

        # Call validate to get generic serializer errors
        try:
            self.validate(data)
        except AvocatoValidationError as e:
            errors['generic'] += e.messages

        return errors

    def _deserialize(self):
        if not self._initial_data:
            raise AvocatoError('Missing data to deserialize')

        errors = {}
        if self.many:
            errors.update(self._validate(data) for data in self._initial_data)
        else:
            errors.update(self._validate(self._initial_data))
        return errors

    def _populate_instance(self, instance, data):
        if self.instance:
            fields = self.update_fields
        else:
            fields = self.create_fields

        for field in fields:
            if not field.required and field._name not in data:
                continue
            setattr(instance, field._name, data[field._name])
        return instance

    def to_instance(self, instance_class=None):
        """Populates an instance with data

        If doesn't exists, it creates a new one and populates it. If it already exists, it updates
        fields with new data.
        """
        if self.many:
            raise AvocatoError('Can not convert serializer with many=True to one instance.')

        if not self._validation_successful:
            raise AvocatoError('Data is invalid or `.is_valid()` has not been run')

        if not self.instance and not instance_class:
            raise AvocatoError('Missing instance or Meta class is missing a model')

        obj = None
        if instance_class:
            obj = instance_class()
        else:
            obj = self.instance
        return self._populate_instance(obj, self._initial_data)

    def is_valid(self):
        """Checks wether data passes validation.

        Returns True if all validations were successful on all fields, otherwise returns False.
        """
        if self.many:
            raise AvocatoError('Validating a serializer with many=True is not supported')
        self.errors = self._deserialize()
        if self.errors:
            self._validation_successful = False
            return False

        self._validation_successful = True
        return True


class DictSerializer(Serializer):
    """Base class for custom ``dict`` serializers.

    Example:

    .. code-block:: python

        class FooSerializer(DictSerializer):
            bar = IntField()
            baz = StrField()

        obj = {'bar': 2, 'baz': 'hello'}
        FooSerializer(obj).data
        # {'bar': 2, 'baz': 'hello'}
    """
    default_getter = operator.itemgetter
