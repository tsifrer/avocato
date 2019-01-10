import pytest

from avocato.exceptions import AvocatoError
from avocato.fields import Field, IntField, MethodField, StrField
from avocato.serializer import DictSerializer, Serializer


class DummyObject(object):
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def test_data_gets_cached_after_first_call():
    class ASerializer(Serializer):
        foo = Field()

    foo = DummyObject(foo=5)
    serializer = ASerializer(foo)
    data1 = serializer.data
    data2 = serializer.data
    assert data1 is data2


def test_serializer_with_callable_field():
    class ASerializer(Serializer):
        foo = Field(call=True)

    obj = DummyObject(foo=lambda: 5)
    assert ASerializer(obj).data['foo'] == 5


def test_serializer_inheritance():
    class ASerializer(Serializer):
        a = Field()

    class CSerializer(Serializer):
        c = Field()

    class ABSerializer(ASerializer):
        b = Field()

    class ABCSerializer(ABSerializer, CSerializer):
        pass

    obj = DummyObject(a=5, b='hello', c=100)
    assert ASerializer(obj).data['a'] == 5
    data = ABSerializer(obj).data
    assert data['a'] == 5
    assert data['b'] == 'hello'
    data = ABCSerializer(obj).data
    assert data['a'] == 5
    assert data['b'] == 'hello'
    assert data['c'] == 100


def test_serializer_with_many():
    class ASerializer(Serializer):
        foo = Field()

    objs = [DummyObject(foo=i) for i in range(5)]
    data = ASerializer(objs, many=True).data
    assert len(data) == 5
    assert data[0]['foo'] == 0
    assert data[1]['foo'] == 1
    assert data[2]['foo'] == 2
    assert data[3]['foo'] == 3
    assert data[4]['foo'] == 4


def test_serializer_as_a_field():
    class ASerializer(Serializer):
        a = Field()

    class BSerializer(Serializer):
        b = ASerializer()

    obj = DummyObject(b=DummyObject(a=3))
    assert BSerializer(obj).data['b']['a'] == 3


def test_serializer_as_a_field_with_many():
    class ASerializer(Serializer):
        a = Field()

    class BSerializer(Serializer):
        b = ASerializer(many=True)

    obj = DummyObject(b=[DummyObject(a=i) for i in range(3)])
    data = BSerializer(obj).data['b']
    assert len(data) == 3
    assert data[0]['a'] == 0
    assert data[1]['a'] == 1
    assert data[2]['a'] == 2


def test_serializer_method_field():
    class ASerializer(Serializer):
        a = MethodField()
        b = MethodField('add_9')

        def get_a(self, obj):
            return obj.a + 5

        def add_9(self, obj):
            return obj.a + 9

    obj = DummyObject(a=2)
    data = ASerializer(obj).data
    assert data['a'] == 7
    assert data['b'] == 11


def test_serializer_dotted_attr():
    class ASerializer(Serializer):
        a = Field('a.b.c')

    obj = DummyObject(a=DummyObject(b=DummyObject(c=2)))
    data = ASerializer(obj).data
    assert data['a'] == 2


def test_serializer_custom_field():
    class Add5Field(Field):
        def to_value(self, value):
            return value + 5

    class ASerializer(Serializer):
        a = Add5Field()

    obj = DummyObject(a=10)
    data = ASerializer(obj).data
    assert data['a'] == 15


@pytest.mark.parametrize('value,expected', [
    (None, None,),
    (5, 5,),
])
def test_serializer_optional_field_does_not_raise(value, expected):
    class ASerializer(Serializer):
        a = IntField(required=False)

    obj = DummyObject(a=value)
    data = ASerializer(obj).data
    assert data['a'] == expected


def test_serializer_optional_field_does_not_raise_if_attribute_is_missing_in_object():
    class ASerializer(Serializer):
        a = Field(required=False)

    obj = DummyObject()
    data = ASerializer(obj).data
    assert 'a' not in data


def test_serializer_required_field_raises():
    class ASerializer(Serializer):
        a = IntField()

    obj = DummyObject(a=None)
    with pytest.raises(AvocatoError) as e:
        ASerializer(obj).data
    assert str(e.value) == "Field a is required, but it's value is None"


def test_serializer_required_field_raises_if_attribute_is_missing_in_object():
    class ASerializer(Serializer):
        a = Field()

    obj = DummyObject()
    with pytest.raises(AvocatoError) as e:
        ASerializer(obj).data
    assert str(e.value) == "Field a is required"


@pytest.mark.parametrize('value,expected', [
    (None, None,),
    (5, 5,),
])
def test_serializer_optional_methodfield_does_not_raise(value, expected):
    class ASerializer(Serializer):
        a = MethodField(required=False)

        def get_a(self, obj):
            return obj.a

    obj = DummyObject(a=value)
    data = ASerializer(obj).data
    assert data['a'] == expected


def test_serializer_required_methodfield_does_not_raise():
    # Required methodfield should not raise an exception if returned value is None as that
    # might be a valid value returned from the method field.
    class ASerializer(Serializer):
        a = MethodField()

        def get_a(self, obj):
            return obj.a

    obj = DummyObject(a=None)
    data = ASerializer(obj).data
    assert data['a'] is None


def test_serializer_with_custom_output_label():
    class ASerializer(Serializer):
        foo = StrField(label='spongebob')
        bar = MethodField(label='patrick')

        def get_bar(self, obj):
            return obj.bar

    obj = DummyObject(foo='squarepants', bar='star')
    data = ASerializer(obj).data

    assert 'foo' not in data
    assert data['spongebob'] == 'squarepants'
    assert 'bar' not in data
    assert data['patrick'] == 'star'


def test_serializer_is_valid_returns_true_if_field_is_missing_in_data_and_is_not_requred():
    class TestSerializer(Serializer):
        foo = StrField(max_length=3)
        bar = StrField(max_length=3, required=False)

    serializer = TestSerializer(data={'foo': 'asd'})
    assert serializer.is_valid() is True


def test_serializer_is_valid_returns_false_if_field_is_missing_in_data():
    class TestSerializer(Serializer):
        foo = StrField(max_length=3)

    serializer = TestSerializer(data={'omg': 'asdf'})
    assert serializer.is_valid() is False
    assert serializer.errors['foo'] == ['This field is required']


def test_serializer_is_valid_returns_false_if_field_is_passed_in_wrong_type():
    class TestSerializer(Serializer):
        foo = StrField(max_length=3)

    serializer = TestSerializer(data={'foo': 1337})
    assert serializer.is_valid() is False
    assert serializer.errors['foo'] == [
        "Value 1337 of type <class 'int'> must be one of <class 'str'> type"
    ]


def test_serializer_is_valid_only_checks_is_create_fields_when_no_instance_is_present():
    class TestSerializer(Serializer):
        foo = StrField(max_length=3, is_create_field=False)
        bar = StrField(max_length=3)

    serializer = TestSerializer(data={'bar': 'baz'})
    assert serializer.is_valid() is True


def test_serializer_is_valid_only_checks_is_update_fields_when_instance_is_present():
    class TestSerializer(Serializer):
        foo = StrField(max_length=3, is_update_field=False)
        bar = StrField(max_length=3)

    obj = DummyObject(bar='wtf')

    serializer = TestSerializer(instance=obj, data={'bar': 'baz'})
    assert serializer.is_valid() is True


def test_serializer_method_validator():
    class TestSerializer(Serializer):
        foo = StrField(max_length=3)

        def validate_foo(self, value):
            assert value == 'asdf'
            raise Exception('Called validate_foo')

    serializer = TestSerializer(data={'foo': 'asdf'})

    with pytest.raises(Exception) as e:
        serializer.is_valid()
    assert str(e.value) == 'Called validate_foo'


def test_serializer_validate_function():
    class TestSerializer(Serializer):
        foo = StrField(max_length=3)

        def validate(self, data):
            assert data == {'foo': 'asdf'}
            raise Exception('Called validate')

    serializer = TestSerializer(data={'foo': 'asdf'})

    with pytest.raises(Exception) as e:
        serializer.is_valid()
    assert str(e.value) == 'Called validate'


def test_serializer_to_instance_does_not_complain_if_non_required_field_is_missing():
    class TestSerializer(Serializer):
        foo = StrField(max_length=3)
        bar = StrField(max_length=3, required=False)

    obj = DummyObject(foo='abc', bar='')
    serializer = TestSerializer(instance=obj, data={'foo': '345'})
    assert serializer.is_valid() is True
    serializer.to_instance()
    assert obj.foo == '345'
    assert obj.bar == ''


def test_serializer_to_instance_raises_error_if_instance_is_missing():
    class TestSerializer(Serializer):
        foo = StrField(max_length=3)
        bar = StrField(max_length=3, required=False)

    serializer = TestSerializer(data={'foo': '345'})
    assert serializer.is_valid() is True

    with pytest.raises(AvocatoError) as e:
        serializer.to_instance()
    assert str(e.value) == 'Missing instance or Meta class is missing a model'


def test_serializer_to_instance_raises_error_if_validation_was_not_successful():
    class TestSerializer(Serializer):
        foo = StrField(max_length=3)
        bar = StrField(max_length=3, required=False)

    serializer = TestSerializer(data={'foo': '345'})
    with pytest.raises(AvocatoError) as e:
        serializer.to_instance()
    assert str(e.value) == 'Data is invalid or `.is_valid()` has not been run'


def test_dict_serializer():
    class ASerializer(DictSerializer):
        a = IntField()
        b = Field(attr='foo')

    obj = {'a': '2', 'foo': 'hello'}
    data = ASerializer(obj).data
    assert data['a'] == 2
    assert data['b'] == 'hello'


def test_dict_serializer_with_many():
    class ASerializer(DictSerializer):
        a = IntField()
        b = Field(attr='foo')

    stuff = [
        {'a': 2, 'foo': 'hello'},
        {'a': 5, 'foo': 'bar'}
    ]
    data = ASerializer(stuff, many=True).data
    assert len(data) == 2
    assert data[0]['a'] == 2
    assert data[0]['b'] == 'hello'
    assert data[1]['a'] == 5
    assert data[1]['b'] == 'bar'


@pytest.mark.parametrize('value,expected', [
    (None, None,),
    (5, 5,),
])
def test_dict_serializer_optional_field_does_not_raise(value, expected):
    class ASerializer(DictSerializer):
        a = IntField(required=False)

    data = ASerializer({'a': value}).data
    assert data['a'] == expected


def test_dict_serializer_optional_field_does_not_raise_if_attribute_is_missing_in_object():
    class ASerializer(DictSerializer):
        a = Field(required=False)

    data = ASerializer({}).data
    assert 'a' not in data


def test_dict_serializer_required_field_raises():
    class ASerializer(DictSerializer):
        a = IntField()

    with pytest.raises(AvocatoError) as e:
        ASerializer({'a': None}).data
    assert str(e.value) == "Field a is required, but it's value is None"


def test_dict_serializer_required_field_raises_if_attribute_is_missing_in_object():
    class ASerializer(DictSerializer):
        a = Field()

    with pytest.raises(AvocatoError) as e:
        ASerializer({}).data
    assert str(e.value) == 'Field a is required'
