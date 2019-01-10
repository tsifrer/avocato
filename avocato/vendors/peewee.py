import peewee

from playhouse import postgres_ext

from ..exceptions import AvocatoError
from ..fields import (
    BoolField,
    DateTimeField,
    DecimalField,
    DictField,
    FloatField,
    IntField,
    StrField,
)
from ..serializer import Serializer, SerializerMeta


class PeeWeeSerializerMeta(SerializerMeta):

    _field_mapping = {
        peewee.IntegerField: IntField,
        peewee.BigIntegerField: IntField,
        peewee.SmallIntegerField: IntField,
        peewee.AutoField: IntField,
        peewee.BigAutoField: IntField,
        peewee.IdentityField: IntField,
        peewee.FloatField: FloatField,
        peewee.DoubleField: FloatField,
        peewee.DecimalField: DecimalField,
        peewee.CharField: StrField,
        peewee.FixedCharField: StrField,
        peewee.TextField: StrField,
        peewee.BooleanField: BoolField,
        peewee.DateTimeField: DateTimeField,
        postgres_ext.HStoreField: DictField,
    }

    _not_supported = [
        peewee.BareField,
        peewee.BigBitField,
        peewee.BinaryUUIDField,
        peewee.BitField,
        peewee.BlobField,
        peewee.DateField,
        peewee.ForeignKeyField,
        peewee.IPField,
        peewee.TimeField,
        peewee.TimestampField,
        peewee.UUIDField,
    ]

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
            peewee_field = getattr(Model, field_name)
            if type(peewee_field) in cls._not_supported:
                raise AvocatoError('{} is not supported by avocato'.format(type(peewee_field)))
            field = cls._field_mapping[type(peewee_field)]

            # peewee name: avocato name
            extra_kwarg_mapping = {
                'max_length': 'max_length',
            }
            extra_kwargs = {}
            for peewee_kw_name, avocato_kw_name in extra_kwarg_mapping.items():
                try:
                    extra_kwargs[avocato_kw_name] = getattr(peewee_field, peewee_kw_name)
                except AttributeError:
                    pass

            fields[field_name] = field(
                attr=field_name,
                label=field_name,
                required=not peewee_field.null,
                is_create_field=field_name in create_fields,
                is_update_field=field_name in update_fields,
                validators=None,
                **extra_kwargs
            )

        return Model, field_names, fields


class PeeWeeModelSerializer(Serializer, metaclass=PeeWeeSerializerMeta):
    """Class for converting to and from simple Python datatypes to peewee models.

    Example:

    .. code-block:: python

        class ModelFoo(peewee.Model):
            bar = peewee.IntegerField()
            baz = peewee.CharField()

        class FooSerializer(PeeweeModelSerializer):
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
        """Saves the instance with the help of peewee models ``.save()`` method.
        """
        if not self.instance:
            obj = self.to_instance(self._meta_model)
            self.instance = obj
            return self.create(self._initial_data)
        else:
            self.to_instance()
            return self.update(self._initial_data)
