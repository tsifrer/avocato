import operator
from collections import defaultdict

from .exceptions import AvocatoError, AvocatoValidationError
from .fields import Field


class Object(object):
    pass


# TODO: try and refactor this
def _compile_fields(field, name, object_cls):
    getter = field.as_getter(name, object_cls)
    if getter is None:
        getter = operator.itemgetter(field.attr or name)

    # Set the field name to a supplied label; defaults to the attribute name.
    field._name = name
    field._getter = getter
    return field


class AvocatoObjectMeta(type):
    @staticmethod
    def _get_fields_from_base_classes(object_cls):
        fields = []
        # Get all the fields from base classes.
        for cls in object_cls.__mro__[::-1]:
            if isinstance(cls, AvocatoObjectMeta):
                fields += cls._fields
        return fields

    @staticmethod
    def _compile_fields(field_map, object_cls):
        return [
            _compile_fields(field, name, object_cls)
            for name, field in field_map.items()
        ]

    @staticmethod
    def parse_meta_class(cls, meta_cls, direct_fields):
        return None, None

    # def __call__(cls, *args, **kwargs):
    #     obj = super().__call__(*args, **kwargs)
    #     # Set fields on object and set default values
    #     for field in obj._fields:
    #         setattr(obj, field._name, field.default)
    #     return obj

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

        meta_model = Object
        if "Meta" in attrs:
            meta_model, meta_fields = cls.parse_meta_class(
                cls, attrs["Meta"], direct_fields
            )
            del attrs["Meta"]

        meta_fields.update(direct_fields)

        real_cls = super().__new__(cls, name, bases, attrs)
        compiled_fields = cls._compile_fields(meta_fields, real_cls)

        base_classes_fields = cls._get_fields_from_base_classes(real_cls)

        real_cls._meta_model = meta_model
        all_fields = compiled_fields + base_classes_fields
        real_cls._fields = all_fields
        real_cls._field_names = [field._name for field in all_fields]
        # real_cls.create_fields = [field for field in all_fields if field.is_create_field]
        # real_cls.update_fields = [field for field in all_fields if field.is_update_field]
        return real_cls


class AvocatoObject(Field, metaclass=AvocatoObjectMeta):
    """Base class

    ``AvocatoObject`` can be used as a Field to create nested schemas. An object is defined by
    subclassing AvocatoObject and adding each Field as a class variable:

    Example:

    .. code-block:: python

        class MyObject(object):
            bar = 2
            baz = 'hello'

        class FooObject(AvocatoObject):
            bar = IntField()
            baz = StrField()

        obj = MyObject()
        FooObject(obj).data
        # {'bar': 2, 'baz': 'hello'}
    """

    _fields = []
    # create_fields = []
    # update_fields = []
    _validation_successful = False

    #: The default getter used if :meth:`Field.as_getter` returns None.
    # _default_getter = operator.attrgetter

    def __init__(self, data=None, instance=None, many=False, **kwargs):
        """
        :param object instance: instance which we want to serialize. Note that this instance will
                                get directly modified
        """
        super().__init__(**kwargs)
        self.instance = instance or self._meta_model()
        self._data = data
        self._many = many
        self.serialized_data = None
        self.errors = {}

        self._populate_instance()

    def __getattribute__(self, name):
        if name not in {"_field_names", "instance"} and name in self._field_names:
            return getattr(self.instance, name)
        else:
            return super().__getattribute__(name)

    def __setattr__(self, name, value):
        if name in self._field_names:
            setattr(self.instance, name, value)
        else:
            super().__setattr__(name, value)

    def _populate_instance(self):
        for field in self._fields:
            value = None
            if self._data:
                try:
                    value = field._getter(self._data)
                except KeyError:
                    # field value is missing from _data, so use the default one that is set at the start
                    pass

            if value is None and self.instance is not None:
                value = getattr(self.instance, field._name, None)

            if value is None:
                value = field.default

            setattr(self.instance, field._name, value)

    # def _serialize(self, instance, fields):
    #     v = {}
    #     for field in fields:
    #         if field.getter_takes_serializer:
    #             result = field._getter(self, instance)
    #         else:
    #             try:
    #                 result = field._getter(instance)
    #                 if field.call:
    #                     result = result()
    #             except (KeyError, AttributeError):
    #                 if field.required:
    #                     raise AvocatoError('Field {} is required'.format(field._name))
    #                 else:
    #                     continue

    #             if field.required and result is None:
    #                 raise AvocatoError(
    #                     "Field {} is required, but it's value is None".format(field._name)
    #                 )

    #             if result is not None:
    #                 result = field.to_value(result)
    #         v[field._name] = result
    #     return v

    # def to_value(self, instance):
    #     if self.many:
    #         if not instance or not isinstance(instance, Iterable):
    #             return []
    #         serialize = self._serialize
    #         return [serialize(o, self._fields) for o in instance]
    #     return self._serialize(instance, self._fields)

    # @property
    # def data(self):
    #     """Get the serialized data from the :class:`Serializer`.

    #     The data will be cached for future accesses.
    #     """
    #     if self._serialized_data is None:
    #         self._serialized_data = self.to_value(self.instance)
    #     return self._serialized_data

    # def validate(self, data):
    #     pass

    # # def _populate_instance(self, instance, data):
    # #     if self.instance:
    # #         fields = self.update_fields
    # #     else:
    # #         fields = self.create_fields

    # #     for field in fields:
    # #         if not field.required and field._name not in data:
    # #             continue
    # #         setattr(instance, field._name, data[field._name])
    # #     return instance

    # def to_instance(self, instance_class=None):
    #     raise NotImplementedError()
    # #     """Populates an instance with data

    # #     If doesn't exists, it creates a new one and populates it. If it already exists, it updates
    # #     fields with new data.
    # #     """
    # #     if self.many:
    # #         raise AvocatoError('Can not convert serializer with many=True to one instance.')

    # #     if not self._validation_successful:
    # #         raise AvocatoError('Data is invalid or `.is_valid()` has not been run')

    # #     if not self.instance and not instance_class:
    # #         raise AvocatoError('Missing instance or Meta class is missing a model')

    # #     obj = None
    # #     if instance_class:
    # #         obj = instance_class()
    # #     else:
    # #         obj = self.instance
    # #     return self._populate_instance(obj, self._initial_data)

    def _validate(self):
        errors = defaultdict(list)
        for field in self._fields:
            field_value = getattr(self.instance, field._name)
            # Loop trough all validators on field and executed them
            if field.validators:
                for validator in field.validators:
                    try:
                        validator(field_value)
                    except AvocatoValidationError as e:
                        errors[field._name] += e.messages
                        break

            # Call validate_<field> if it exist to get field specific errors
            try:
                validate_func = getattr(self, "validate_{0}".format(field._name))
            except AttributeError:
                pass
            else:
                try:
                    validate_func(field_value)
                except AvocatoValidationError as e:
                    errors[field._name] += e.messages

        # # Call validate to get generic serializer errors
        # try:
        #     self.validate(self.instance)
        # except AvocatoValidationError as e:
        #     errors['generic'] += e.messages

        return dict(errors)

    def is_valid(self):
        """Checks wether data passes validation.

        Returns True if all validations were successful on all fields, otherwise returns False.
        """
        if self._many:
            raise AvocatoError(
                "Validating an object with many=True is not supported"
            )

        self.errors = self._validate()
        if self.errors:
            self._validation_successful = False
            return False

        self._validation_successful = True
        return True

    def to_dict(self):
        if not self._validation_successful:
            raise AvocatoError("Data is invalid or `.is_valid()` has not been run")
        data = {}
        for field in self._fields:
            data[field.label or field._name] = getattr(self.instance, field._name)
            # if field.getter_takes_serializer:
            #     result = field._getter(self, instance)
            # else:
            #     try:
            #         result = field._getter(instance)
            #         if field.call:
            #             result = result()
            #     except (KeyError, AttributeError):
            #         if field.required:
            #             raise AvocatoError('Field {} is required'.format(field._name))
            #         else:
            #             continue

            #     if field.required and result is None:
            #         raise AvocatoError(
            #             "Field {} is required, but it's value is None".format(field._name)
            #         )

            #     if result is not None:
            #         result = field.to_value(result)
            # v[field._name] = result
        return data
