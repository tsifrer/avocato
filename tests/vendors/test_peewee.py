from datetime import datetime
from decimal import Decimal

import peewee

from playhouse import postgres_ext

import pytest

from avocato.exceptions import AvocatoError
from avocato.fields import IntField, MethodField
from avocato.validators import Length
from avocato.vendors.peewee import PeeWeeModelSerializer


class ModelA(peewee.Model):
    name = peewee.CharField(max_length=256)
    created_at = peewee.DateTimeField(default=datetime.now)


class ModelB(peewee.Model):
    model_a = peewee.ForeignKeyField(ModelA)
    title = peewee.CharField(max_length=5)
    speed = peewee.IntegerField()


@pytest.mark.parametrize('field,value,expected,expected_type', [
    (peewee.IntegerField(), 5, 5, int),
    (peewee.BigIntegerField(), 5, 5, int),
    (peewee.SmallIntegerField(), 5, 5, int),
    (peewee.AutoField(), 5, 5, int),
    (peewee.BigAutoField(), 5, 5, int),
    (peewee.IdentityField(), 5, 5, int),
    (peewee.FloatField(), 5.5, 5.5, float),
    (peewee.DoubleField(), 5.5, 5.5, float),
    (peewee.DecimalField(), Decimal('13.37'), '13.37', str),
    (peewee.CharField(), 'foo', 'foo', str),
    (peewee.FixedCharField(), 'foo', 'foo', str),
    (peewee.TextField(), 'foo', 'foo', str),
    (peewee.BooleanField(), True, True, bool),
    (peewee.DateTimeField(), datetime(2018, 11, 1), '2018-11-01T00:00:00', str),
    (postgres_ext.HStoreField(), {'foo': 'bar'}, {'foo': 'bar'}, dict),
])
def test_field_is_correctly_serialized(field, value, expected, expected_type):
    class TestModel(peewee.Model):
        foo = field

    class TestSerializer(PeeWeeModelSerializer):
        class Meta:
            model = TestModel
            fields = ['foo']

    instance = TestModel(foo=value)
    serializer = TestSerializer(instance=instance)
    assert serializer.data['foo'] == expected
    assert type(serializer.data['foo']) == expected_type


def test_field_overriding_takes_the_one_from_class():
    class TestSerializer(PeeWeeModelSerializer):
        name = IntField()

        class Meta:
            model = ModelA
            fields = ['name']

    instance = ModelA(name='1234')
    serializer = TestSerializer(instance=instance)
    assert serializer.data['name'] == 1234
    assert type(serializer.data['name']) == int


def test_foreign_key_serialization():
    class TestSerializer(PeeWeeModelSerializer):
        model_a = IntField(attr='model_a_id')

        class Meta:
            model = ModelB
            fields = ['model_a']

    model_a = ModelA(id=1337)
    instance = ModelB(model_a=model_a)
    serializer = TestSerializer(instance=instance)
    assert serializer.data['model_a'] == 1337


def test_additinal_fields_that_are_not_on_model():
    class TestSerializer(PeeWeeModelSerializer):
        extras = MethodField()

        class Meta:
            model = ModelA
            fields = ['name', 'extras']

        def get_extras(self, obj):
            return 'patrick star'

    instance = ModelA(name='spongebob')
    serializer = TestSerializer(instance=instance)
    assert serializer.data['name'] == 'spongebob'
    assert serializer.data['extras'] == 'patrick star'


def test_raises_exception_if_field_defined_but_not_in_meta_fields():
    with pytest.raises(AvocatoError) as e:
        class TestSerializer(PeeWeeModelSerializer):
            extras = MethodField()

            class Meta:
                model = ModelA
                fields = ['name']

            def get_extras(self, obj):
                return 'patrick star'

    assert str(e.value) == "Fields ['extras'] are missing in Meta class"


def test_raises_attributeerror_if_model_is_not_defined_in_meta():
    with pytest.raises(AttributeError) as e:
        class TestSerializer(PeeWeeModelSerializer):
            class Meta:
                fields = ['name']
    assert str(e.value) == "type object 'Meta' has no attribute 'model'"


def test_raises_attributeerror_if_fields_are_not_defined_in_meta():
    with pytest.raises(AttributeError) as e:
        class TestSerializer(PeeWeeModelSerializer):
            class Meta:
                model = ModelA
    assert str(e.value) == "type object 'Meta' has no attribute 'fields'"


@pytest.mark.parametrize('null,required', [
    (False, True),
    (True, False),
])
def tests_fields_have_required_attribute_set_correctly(null, required):
    class TestModel(peewee.Model):
        foo = peewee.CharField(null=null)

    class TestSerializer(PeeWeeModelSerializer):
        class Meta:
            model = TestModel
            fields = ['foo']

    instance = TestModel(foo='spongebob')
    serializer = TestSerializer(instance=instance)
    assert serializer.fields[0].required == required


def test_max_length_validator_is_added_to_fields():
    class TestModel(peewee.Model):
        foo = peewee.CharField(max_length=1337)

    class TestSerializer(PeeWeeModelSerializer):
        class Meta:
            model = TestModel
            fields = ['foo']

    instance = TestModel(foo='spongebob')
    serializer = TestSerializer(instance=instance)
    validators = serializer.fields[0].validators
    validator = [v for v in validators if isinstance(v, Length)]
    assert len(validator) == 1
    validator = validator[0]
    assert validator.max_length == 1337
    assert validator.min_length is None
    assert validator.equal is None


def test_nested():
    class SerializerA(PeeWeeModelSerializer):
        class Meta:
            model = ModelA
            fields = ['id', 'name']

    class SerializerB(PeeWeeModelSerializer):
        model_a = SerializerA()

        class Meta:
            model = ModelB
            fields = ['model_a', 'title']

    instance_a = ModelA(id=1337, name='spongebob')
    instance = ModelB(model_a=instance_a, title='patrick star')
    serializer = SerializerB(instance)

    assert serializer.data == {
        'title': 'patrick star',
        'model_a': {
            'id': 1337,
            'name': 'spongebob'
        }
    }


def test_create_object_in_db(mocker):
    class SerializerA(PeeWeeModelSerializer):
        class Meta:
            model = ModelA
            fields = ['name']

    serializer = SerializerA(data={'name': 'spongebob'})
    assert serializer.is_valid()
    save_mock = mocker.patch('peewee.Model.save')
    serializer.save()
    assert save_mock.call_count == 1
    assert serializer.instance.name == 'spongebob'


def test_update_object_in_db(mocker):
    class SerializerA(PeeWeeModelSerializer):
        class Meta:
            model = ModelA
            fields = ['name']

    instance = ModelA(name='patrick')
    serializer = SerializerA(instance=instance, data={'name': 'spongebob'})
    assert serializer.is_valid()
    save_mock = mocker.patch('peewee.Model.save')
    serializer.save()
    assert save_mock.call_count == 1
    assert serializer.instance.name == 'spongebob'


def test_create_returns_created_object(mocker):
    class SerializerA(PeeWeeModelSerializer):
        class Meta:
            model = ModelA
            fields = ['name']

    serializer = SerializerA(data={'name': 'spongebob'})
    assert serializer.is_valid()
    save_mock = mocker.patch('peewee.Model.save')
    obj = serializer.save()
    assert save_mock.call_count == 1
    assert obj is not None
    assert obj.name == 'spongebob'


def test_update_returns_updated_object(mocker):
    class SerializerA(PeeWeeModelSerializer):
        class Meta:
            model = ModelA
            fields = ['name']

    instance = ModelA(name='patrick')
    serializer = SerializerA(instance=instance, data={'name': 'spongebob'})
    assert serializer.is_valid()
    save_mock = mocker.patch('peewee.Model.save')
    obj = serializer.save()
    assert save_mock.call_count == 1
    assert obj is not None
    assert obj.name == 'spongebob'


def test_is_valid_only_checks_create_fields_when_no_instance_is_present():
    class TestSerializer(PeeWeeModelSerializer):
        class Meta:
            model = ModelB
            fields = ['title', 'speed']
            create_fields = ['speed']

    data = {'speed': 1337}
    serializer = TestSerializer(data=data)
    assert serializer.is_valid() is True


def test_is_valid_only_checks_update_fields_when_instance_is_present():
    class TestSerializer(PeeWeeModelSerializer):
        class Meta:
            model = ModelB
            fields = ['title', 'speed']
            update_fields = ['speed']

    instance = ModelB(title='1234', speed=1)
    data = {'speed': 1337}
    serializer = TestSerializer(instance=instance, data=data)
    assert serializer.is_valid() is True


def test_save_only_updates_update_fields_when_instance_is_present(mocker):
    class TestSerializer(PeeWeeModelSerializer):
        class Meta:
            model = ModelB
            fields = ['title', 'speed']
            update_fields = ['speed']

    instance = ModelB(title='1234', speed=1)
    data = {'speed': 1337}
    serializer = TestSerializer(instance=instance, data=data)
    assert serializer.is_valid() is True
    save_mock = mocker.patch('peewee.Model.save')
    serializer.save()
    assert save_mock.call_count == 1
    assert serializer.instance.title == '1234'
    assert serializer.instance.speed == 1337


def test_save_only_updates_create_fields_when_no_instance_is_present(mocker):
    class TestSerializer(PeeWeeModelSerializer):
        class Meta:
            model = ModelB
            fields = ['title', 'speed']
            create_fields = ['speed']

    data = {'speed': 1337}
    serializer = TestSerializer(data=data)
    assert serializer.is_valid() is True
    save_mock = mocker.patch('peewee.Model.save')
    serializer.save()
    assert save_mock.call_count == 1
    assert serializer.instance.title is None
    assert serializer.instance.speed == 1337
