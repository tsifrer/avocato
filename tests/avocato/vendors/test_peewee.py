from datetime import datetime

import peewee

import pytest

from avocato.fields import StrField, IntField
from avocato.validators import Length
from avocato.vendors.peewee import PeeWeeModelObject
from avocato.objects import AvocatoObject


class ModelA(peewee.Model):
    name = peewee.CharField(max_length=256)
    created_at = peewee.DateTimeField(default=datetime.now)


class ModelB(peewee.Model):
    model_a = peewee.ForeignKeyField(ModelA)
    title = peewee.CharField(max_length=5)
    speed = peewee.IntegerField()


def test_additinal_fields_that_are_not_on_model():
    class TestObject(PeeWeeModelObject):
        extras = StrField(default="patrick star")

        class Meta:
            model = ModelA

    instance = ModelA(name="spongebob")
    obj = TestObject(instance=instance)

    assert obj.name == "spongebob"
    assert obj.extras == "patrick star"


def test_raises_attributeerror_if_model_is_not_defined_in_meta():
    with pytest.raises(AttributeError) as e:

        class TestObject(PeeWeeModelObject):
            class Meta:
                pass

    assert str(e.value) == "type object 'Meta' has no attribute 'model'"


@pytest.mark.parametrize("null,required", [(False, True), (True, False)])
def tests_fields_have_required_attribute_set_correctly(null, required):
    class TestModel(peewee.Model):
        id = peewee.CharField(null=null)

    class TestObject(PeeWeeModelObject):
        class Meta:
            model = TestModel

    instance = TestModel(foo="spongebob")
    obj = TestObject(instance=instance)
    assert obj._fields[0].required == required


def test_max_length_validator_is_added_to_fields():
    class TestModel(peewee.Model):
        id = peewee.CharField(max_length=1337)

    class TestObject(PeeWeeModelObject):
        class Meta:
            model = TestModel

    instance = TestModel(foo="spongebob")
    obj = TestObject(instance=instance)
    validators = obj._fields[0].validators
    validator = [v for v in validators if isinstance(v, Length)]
    assert len(validator) == 1
    validator = validator[0]
    assert validator.max_length == 1337
    assert validator.min_length is None
    assert validator.equal is None


# def test_nested():
#     class ObjectA(PeeWeeModelObject):
#         class Meta:
#             model = ModelA

#     class ObjectB(PeeWeeModelObject):
#         model_a = ObjectA()

#         class Meta:
#             model = ModelB

#     instance_a = ModelA(id=1337, name='spongebob')
#     instance = ModelB(model_a=instance_a, title='patrick star')
#     obj = ObjectB(instance)

#     assert obj.to_dict() == {
#         'title': 'patrick star',
#         'model_a': {
#             'id': 1337,
#             'name': 'spongebob'
#         }
#     }


def test_create_object_in_db(mocker):
    class ObjectA(PeeWeeModelObject):
        class Meta:
            model = ModelA

    obj = ObjectA(data={"name": "spongebob"})
    assert obj.is_valid()
    save_mock = mocker.patch("peewee.Model.save")
    obj.save()
    assert save_mock.call_count == 1
    assert obj.instance.name == "spongebob"


def test_update_object_in_db(mocker):
    class ObjectA(PeeWeeModelObject):
        class Meta:
            model = ModelA

    instance = ModelA(name="patrick")
    obj = ObjectA(instance=instance, data={"name": "spongebob"})
    assert obj.is_valid()
    save_mock = mocker.patch("peewee.Model.save")
    obj.save()
    assert save_mock.call_count == 1
    assert obj.instance.name == "spongebob"


def test_object_populates_new_instance_on_init():
    class ModelFoo(peewee.Model):
        title = peewee.CharField(max_length=5)
        speed = peewee.IntegerField()

    class FooObj(AvocatoObject):
        title = StrField(attr="spongebob")
        speed = IntField()

    class InheritedObject(PeeWeeModelObject, FooObj):
        class Meta:
            model = ModelFoo

    obj = InheritedObject({"speed": 1337, "title": "1234"})
    assert isinstance(obj.instance, ModelFoo)
    assert obj.instance.title == "1234"
    assert obj.instance.speed == 1337
