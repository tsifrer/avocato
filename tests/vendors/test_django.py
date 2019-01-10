from datetime import datetime
from decimal import Decimal

from django.contrib.postgres import fields as psql_fields
from django.db import models

import pytest

from avocato.exceptions import AvocatoError
from avocato.fields import IntField, MethodField
from avocato.validators import Length, OneOf
from avocato.vendors.django import DjangoModelSerializer


@pytest.fixture(scope='function')
def django_setup(tmpdir, monkeypatch):
    from django.conf import settings
    import django
    if not settings.configured:
        settings.configure(DEBUG=True, INSTALLED_APPS=('tests.vendors.test_django',))
        django.setup()


@pytest.fixture(scope='function')
def django_test_models():
    class ModelA(models.Model):
        name = models.CharField(max_length=256)
        created_at = models.DateTimeField(default=datetime.now)

    class ModelB(models.Model):
        model_a = models.ForeignKey(ModelA, on_delete=models.PROTECT)
        title = models.CharField(max_length=5)
        speed = models.IntegerField()

    return ModelA, ModelB


@pytest.mark.parametrize('field,value,expected,expected_type', [
    (models.AutoField(primary_key=True), 5, 5, int),
    (models.BigAutoField(primary_key=True), 5, 5, int),
    (models.BigIntegerField(), 5, 5, int),
    (models.BooleanField(), True, True, bool),
    (models.CharField(), 'foo', 'foo', str),
    (models.DateTimeField(), datetime(2018, 11, 1), '2018-11-01T00:00:00', str),
    (models.DecimalField(), Decimal('13.37'), '13.37', str),
    (models.EmailField(), 'foo@foo.bar', 'foo@foo.bar', str),
    (models.FloatField(), 5.5, 5.5, float),
    (models.IntegerField(), 5, 5, int),
    (models.NullBooleanField(), True, True, bool),
    (models.PositiveIntegerField(), 5, 5, int),
    (models.PositiveSmallIntegerField(), 5, 5, int),
    (models.SlugField(), 'foo', 'foo', str),
    (models.SmallIntegerField(), 5, 5, int),
    (models.TextField(), 'foo', 'foo', str),
    (psql_fields.HStoreField(), {'foo': 'bar'}, {'foo': 'bar'}, dict),
])
def test_field_is_correctly_serialized(field, value, expected, expected_type, django_setup):
    class TestModel(models.Model):
        foo = field

    class TestSerializer(DjangoModelSerializer):
        class Meta:
            model = TestModel
            fields = ['foo']

    instance = TestModel(foo=value)
    serializer = TestSerializer(instance=instance)
    assert serializer.data['foo'] == expected
    assert type(serializer.data['foo']) == expected_type


def test_field_overriding_takes_the_one_from_class(django_test_models):
    ModelA, _ = django_test_models

    class TestSerializer(DjangoModelSerializer):
        name = IntField()

        class Meta:
            model = ModelA
            fields = ['name']

    instance = ModelA(name='1234')
    serializer = TestSerializer(instance=instance)
    assert serializer.data['name'] == 1234
    assert type(serializer.data['name']) == int


def test_foreign_key_serialization(django_test_models):
    ModelA, ModelB = django_test_models

    class TestSerializer(DjangoModelSerializer):
        model_a = IntField(attr='model_a_id')

        class Meta:
            model = ModelB
            fields = ['model_a']

    model_a = ModelA(id=1337)
    instance = ModelB(model_a=model_a)
    serializer = TestSerializer(instance=instance)
    assert serializer.data['model_a'] == 1337


def test_additinal_fields_that_are_not_on_model(django_test_models):
    ModelA, ModelB = django_test_models

    class TestSerializer(DjangoModelSerializer):
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


def test_raises_exception_if_field_defined_but_not_in_meta_fields(django_test_models):
    ModelA, ModelB = django_test_models

    with pytest.raises(AvocatoError) as e:
        class TestSerializer(DjangoModelSerializer):
            extras = MethodField()

            class Meta:
                model = ModelA
                fields = ['name']

            def get_extras(self, obj):
                return 'patrick star'

    assert str(e.value) == "Fields ['extras'] are missing in Meta class"


def test_raises_attributeerror_if_model_is_not_defined_in_meta():
    with pytest.raises(AttributeError) as e:
        class TestSerializer(DjangoModelSerializer):
            class Meta:
                fields = ['name']
    assert str(e.value) == "type object 'Meta' has no attribute 'model'"


def test_raises_attributeerror_if_fields_are_not_defined_in_meta(django_test_models):
    ModelA, ModelB = django_test_models

    with pytest.raises(AttributeError) as e:
        class TestSerializer(DjangoModelSerializer):
            class Meta:
                model = ModelA
    assert str(e.value) == "type object 'Meta' has no attribute 'fields'"


@pytest.mark.parametrize('null,required', [
    (False, True),
    (True, False),
])
def tests_fields_have_required_attribute_set_correctly(null, required):
    class TestModel(models.Model):
        foo = models.CharField(null=null)

    class TestSerializer(DjangoModelSerializer):
        class Meta:
            model = TestModel
            fields = ['foo']

    instance = TestModel(foo='spongebob')
    serializer = TestSerializer(instance=instance)
    assert serializer.fields[0].required == required


def test_max_length_validator_is_added_to_fields():
    class TestModel(models.Model):
        foo = models.CharField(max_length=1337)

    class TestSerializer(DjangoModelSerializer):
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


def test_one_of_validator_is_added_to_fields():
    class TestModel(models.Model):
        foo = models.CharField(choices=(('foo', 'FOO'), ('bar', 'BAR')))

    class TestSerializer(DjangoModelSerializer):
        class Meta:
            model = TestModel
            fields = ['foo']

    instance = TestModel(foo='spongebob')
    serializer = TestSerializer(instance=instance)
    validators = serializer.fields[0].validators
    validator = [v for v in validators if isinstance(v, OneOf)]
    assert len(validator) == 1
    validator = validator[0]
    assert validator.choices == ['foo', 'bar']


def test_create_object_in_db(mocker, django_test_models):
    ModelA, ModelB = django_test_models

    class SerializerA(DjangoModelSerializer):
        class Meta:
            model = ModelA
            fields = ['name']

    serializer = SerializerA(data={'name': 'spongebob'})
    assert serializer.is_valid()
    save_mock = mocker.patch('django.db.models.Model.save')
    serializer.save()
    assert save_mock.call_count == 1
    assert serializer.instance.name == 'spongebob'


def test_update_object_in_db(mocker, django_test_models):
    ModelA, ModelB = django_test_models

    class SerializerA(DjangoModelSerializer):
        class Meta:
            model = ModelA
            fields = ['name']

    instance = ModelA(name='patrick')
    serializer = SerializerA(instance=instance, data={'name': 'spongebob'})
    assert serializer.is_valid()
    save_mock = mocker.patch('django.db.models.Model.save')
    serializer.save()
    assert save_mock.call_count == 1
    assert serializer.instance.name == 'spongebob'


def test_create_returns_created_object(mocker, django_test_models):
    ModelA, ModelB = django_test_models

    class SerializerA(DjangoModelSerializer):
        class Meta:
            model = ModelA
            fields = ['name']

    serializer = SerializerA(data={'name': 'spongebob'})
    assert serializer.is_valid()
    save_mock = mocker.patch('django.db.models.Model.save')
    obj = serializer.save()
    assert save_mock.call_count == 1
    assert obj is not None
    assert obj.name == 'spongebob'


def test_update_returns_updated_object(mocker, django_test_models):
    ModelA, ModelB = django_test_models

    class SerializerA(DjangoModelSerializer):
        class Meta:
            model = ModelA
            fields = ['name']

    instance = ModelA(name='patrick')
    serializer = SerializerA(instance=instance, data={'name': 'spongebob'})
    assert serializer.is_valid()
    save_mock = mocker.patch('django.db.models.Model.save')
    obj = serializer.save()
    assert save_mock.call_count == 1
    assert obj is not None
    assert obj.name == 'spongebob'


def test_is_valid_only_checks_create_fields_when_no_instance_is_present(django_test_models):
    ModelA, ModelB = django_test_models

    class TestSerializer(DjangoModelSerializer):
        class Meta:
            model = ModelB
            fields = ['title', 'speed']
            create_fields = ['speed']

    data = {'speed': 1337}
    serializer = TestSerializer(data=data)
    assert serializer.is_valid() is True


def test_is_valid_only_checks_update_fields_when_instance_is_present(django_test_models):
    ModelA, ModelB = django_test_models

    class TestSerializer(DjangoModelSerializer):
        class Meta:
            model = ModelB
            fields = ['title', 'speed']
            update_fields = ['speed']

    instance = ModelB(title='1234', speed=1)
    data = {'speed': 1337}
    serializer = TestSerializer(instance=instance, data=data)
    assert serializer.is_valid() is True


def test_save_only_updates_update_fields_when_instance_is_present(mocker, django_test_models):
    ModelA, ModelB = django_test_models

    class TestSerializer(DjangoModelSerializer):
        class Meta:
            model = ModelB
            fields = ['title', 'speed']
            update_fields = ['speed']

    instance = ModelB(title='1234', speed=1)
    data = {'speed': 1337}
    serializer = TestSerializer(instance=instance, data=data)
    assert serializer.is_valid() is True
    save_mock = mocker.patch('django.db.models.Model.save')
    serializer.save()
    assert save_mock.call_count == 1
    assert serializer.instance.title == '1234'
    assert serializer.instance.speed == 1337


def test_save_only_updates_create_fields_when_no_instance_is_present(mocker, django_test_models):
    ModelA, ModelB = django_test_models

    class TestSerializer(DjangoModelSerializer):
        class Meta:
            model = ModelB
            fields = ['title', 'speed']
            create_fields = ['speed']

    data = {'speed': 1337}
    serializer = TestSerializer(data=data)
    assert serializer.is_valid() is True
    save_mock = mocker.patch('django.db.models.Model.save')
    serializer.save()
    assert save_mock.call_count == 1
    assert serializer.instance.title == ''
    assert serializer.instance.speed == 1337


def test_nested(django_test_models):
    ModelA, ModelB = django_test_models

    class SerializerA(DjangoModelSerializer):
        class Meta:
            model = ModelA
            fields = ['id', 'name']

    class SerializerB(DjangoModelSerializer):
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
