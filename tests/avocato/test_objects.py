import pytest

from avocato.exceptions import AvocatoError
from avocato.fields import IntField, StrField
from avocato.objects import AvocatoObject, Object


def test_object_populates_new_instance_on_init():
    class FooObj(AvocatoObject):
        foo = IntField()
        bar = StrField(attr="spongebob")

    obj = FooObj({"foo": 1337, "spongebob": "1234"})

    assert isinstance(obj.instance, Object)
    assert obj.instance.foo == 1337
    assert obj.instance.bar == "1234"
    with pytest.raises(AttributeError):
        obj.instance.spongebob

    assert obj.foo == 1337
    assert obj.bar == "1234"
    with pytest.raises(AttributeError):
        obj.spongebob


def test_object_populates_new_instance_on_init_with_default_values_if_missing():
    class FooObj(AvocatoObject):
        foo = IntField(default=13456)
        bar = StrField(attr="spongebob", default="squarepants")

    obj = FooObj()
    assert obj.foo == 13456
    assert obj.bar == "squarepants"


def test_object_populates_new_instance_on_init_correctly():
    class FooObj(AvocatoObject):
        foo = IntField(default=13456)
        bar = StrField(attr="spongebob", default="squarepants")

    instance = Object()
    instance.foo = 1337

    obj = FooObj(instance=instance)
    assert obj.foo == 1337
    assert obj.bar == "squarepants"


def test_object_populates_new_instance_on_init_with_default_value_if_missing():
    class FooObj(AvocatoObject):
        foo = IntField(default=13456)
        bar = StrField(attr="spongebob", default="squarepants")

    obj = FooObj({"foo": 1337})
    assert obj.foo == 1337
    assert obj.bar == "squarepants"


def test_objects_setter_sets_value_directly_on_instance():
    class FooObj(AvocatoObject):
        foo = IntField()

    obj = FooObj({"foo": 1337})

    assert obj.instance.foo == 1337
    obj.foo = 123019590148590185
    assert obj.instance.foo == 123019590148590185


def test_object_to_dict_raises_if_is_valid_has_not_been_run():
    class FooObj(AvocatoObject):
        foo = IntField()

    obj = FooObj({"foo": 1337})
    with pytest.raises(AvocatoError) as e:
        obj.to_dict()

    assert str(e.value) == "Data is invalid or `.is_valid()` has not been run"


def test_object_to_dict_raises_if_validation_failed():
    class FooObj(AvocatoObject):
        foo = IntField()

    obj = FooObj({"foo": "1337"})
    assert obj.is_valid() is False
    with pytest.raises(AvocatoError) as e:
        obj.to_dict()

    assert str(e.value) == "Data is invalid or `.is_valid()` has not been run"


def test_object_to_dict_returns_correct_data():
    class FooObj(AvocatoObject):
        foo = IntField()

    obj = FooObj({"foo": 1337})
    assert obj.is_valid()
    assert obj.to_dict() == {"foo": 1337}


def test_object_to_dict_respects_field_label():
    class FooObj(AvocatoObject):
        foo = IntField(label="This is a random label")

    obj = FooObj({"foo": 1337})
    assert obj.is_valid()
    assert obj.to_dict() == {"This is a random label": 1337}
