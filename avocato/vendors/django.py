from django.contrib.postgres import fields as psql_fields
from django.db import models

from ..exceptions import AvocatoError
from ..fields import (
    BoolField,
    DateTimeField,
    DecimalField,
    DictField,
    EmailField,
    FloatField,
    IntField,
    StrField,
)
from ..serializer import Serializer, SerializerMeta


class DjangoSerializerMeta(SerializerMeta):

    _field_mapping = {
        models.AutoField: IntField,
        models.BigAutoField: IntField,
        models.BigIntegerField: IntField,
        models.BooleanField: BoolField,
        models.CharField: StrField,
        models.DateTimeField: DateTimeField,
        models.DecimalField: DecimalField,
        models.EmailField: EmailField,
        models.FloatField: FloatField,
        models.IntegerField: IntField,
        models.NullBooleanField: BoolField,
        models.PositiveIntegerField: IntField,
        models.PositiveSmallIntegerField: IntField,
        models.SlugField: StrField,
        models.SmallIntegerField: IntField,
        models.TextField: StrField,
        psql_fields.HStoreField: DictField,
    }

    _not_supported = [
        models.BinaryField,
        models.DateField,
        models.DurationField,
        models.FileField,
        models.FilePathField,
        models.ImageField,
        models.GenericIPAddressField,
        models.TimeField,
        models.URLField,
        models.UUIDField,
        psql_fields.ArrayField,
        psql_fields.JSONField,
        psql_fields.CIText,
        psql_fields.IntegerRangeField,
        psql_fields.BigIntegerRangeField,
        psql_fields.FloatRangeField,
        psql_fields.DateTimeRangeField,
        psql_fields.DateRangeField,
    ]

    @staticmethod
    def _parse_extra_kwargs(cls, django_field):
        extra_kwargs = {}

        # max_length
        try:
            value = getattr(django_field, 'max_length')
        except AttributeError:
            pass
        else:
            if value:
                extra_kwargs['max_length'] = value

        # choices
        try:
            value = getattr(django_field, 'choices')
        except AttributeError:
            pass
        else:
            if value:
                choices = dict(value)
                extra_kwargs['choices'] = list(choices.keys())
        return extra_kwargs

    @staticmethod
    def parse_meta_class(cls, meta_cls, direct_fields):
        fields = {}
        Model = meta_cls.model
        field_names = meta_cls.fields

        update_fields = field_names
        try:
            update_fields = getattr(meta_cls, 'update_fields')
        except AttributeError:
            pass

        create_fields = field_names
        try:
            create_fields = getattr(meta_cls, 'create_fields')
        except AttributeError:
            pass

        for field_name in field_names:
            # Skip a field if it's defined directly on the serializer
            if field_name in direct_fields:
                continue
            django_field = Model._meta.get_field(field_name)
            if type(django_field) in cls._not_supported:
                raise AvocatoError('{} is not supported by avocato'.format(type(django_field)))
            field = cls._field_mapping[type(django_field)]

            extra_kwargs = cls._parse_extra_kwargs(cls, django_field)

            fields[field_name] = field(
                attr=field_name,
                label=field_name,
                required=not django_field.null,
                validators=None,
                is_create_field=field_name in create_fields,
                is_update_field=field_name in update_fields,
                **extra_kwargs
            )

        return Model, field_names, fields


class DjangoModelSerializer(Serializer, metaclass=DjangoSerializerMeta):
    """Class for converting to and from simple Python datatypes to Django Models.

    Example:

    .. code-block:: python

        class ModelFoo(django.db.models.Model):
            bar = models.IntegerField()
            baz = models.CharField()

        class FooSerializer(DjangoModelSerializer):
            class Meta:
                model = ModelFoo
                fields =['bar', 'baz']

        obj = ModelFoo(bar=2, baz='hello')
        FooSerializer(obj).data
        # {'bar': 2, 'baz': 'hello'}
    """

    def create(self, data):
        """Override this function if you want to do something custom when creating an object.
        """
        self.instance.save()
        return self.instance

    def update(self, data):
        """Override this function if you want to do something custom when updating an object.
        """
        self.instance.save()
        return self.instance

    def save(self):
        """Saves the instance with the help of Django models ``.save()`` method.
        """
        if not self.instance:
            obj = self.to_instance(self._meta_model)
            self.instance = obj
            return self.create(self._initial_data)
        else:
            self.to_instance()
            return self.update(self._initial_data)
