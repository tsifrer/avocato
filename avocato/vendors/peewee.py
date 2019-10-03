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
from ..objects import AvocatoObject, AvocatoObjectMeta


class PeeWeeObjectMeta(AvocatoObjectMeta):

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
        for field_name in Model._meta.fields.keys():
            # Skip a field if it's defined directly on the serializer
            if field_name in direct_fields:
                continue

            peewee_field = getattr(Model, field_name)
            if type(peewee_field) in cls._not_supported:
                raise AvocatoError(
                    "{} is not supported by avocato".format(type(peewee_field))
                )
            field = cls._field_mapping[type(peewee_field)]

            # peewee name: avocato name
            extra_kwarg_mapping = {"max_length": "max_length"}
            extra_kwargs = {}
            for peewee_kw_name, avocato_kw_name in extra_kwarg_mapping.items():
                try:
                    extra_kwargs[avocato_kw_name] = getattr(
                        peewee_field, peewee_kw_name
                    )
                except AttributeError:
                    pass

            required = not peewee_field.null
            # peewee's autofields should not be required as they'll get generated
            # by the database or peewee
            if type(peewee_field) in {peewee.AutoField, peewee.BigAutoField}:
                required = False

            fields[field_name] = field(
                attr=field_name,
                label=field_name,
                required=required,
                validators=None,
                **extra_kwargs
            )

        return Model, fields


class PeeWeeModelObject(AvocatoObject, metaclass=PeeWeeObjectMeta):
    """Class for converting to and from simple Python datatypes to peewee models.

    Example:

    .. code-block:: python

        class ModelFoo(peewee.Model):
            bar = peewee.IntegerField()
            baz = peewee.CharField()

        class FooSerializer(PeeWeeModelObject):
            class Meta:
                model = ModelFoo
                fields =['bar', 'baz']

        obj = ModelFoo(bar=2, baz='hello')
        FooSerializer(obj).data
        # {'bar': 2, 'baz': 'hello'}
    """

    def save(self):
        """Saves the instance with the help of peewee models ``.save()`` method.
        """
        self.instance.save()
        return self.instance
