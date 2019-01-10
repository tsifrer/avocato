from datetime import datetime
from decimal import Decimal

import pytest

from avocato import validators as avocato_validators
from avocato.fields import (
    BoolField, DateTimeField, DecimalField, DictField, EmailField, Field, FloatField, IntField,
    MethodField, StrField
)


@pytest.mark.parametrize('value,expected', [
    (5, 5,),
    ('a', 'a',),
    (None, None,),
])
def test_field_to_value_returns_unmodified_value(value, expected):
    assert Field().to_value(value) == expected


def test_field_as_getter_returns_none():
    assert Field().as_getter(None, None) is None


def test_field_required_adds_validators():
    validators = Field(required=True).validators
    assert len(validators) == 1
    assert isinstance(validators[0], avocato_validators.Required)


def test_accepted_types_field_has_one_of_type_validator():
    class AcceptedTypesField(Field):
        accepted_types = (str,)

    validators = AcceptedTypesField().validators
    assert len(validators) == 2
    assert isinstance(validators[0], avocato_validators.Required)
    assert isinstance(validators[1], avocato_validators.OneOfType)
    assert validators[1].choices == (str,)


@pytest.mark.parametrize('value,expected', [
    (5, '5',),
    ('a', 'a',),
    (None, 'None',),
])
def test_str_field_to_value_returns_str(value, expected):
    result = StrField().to_value(value)
    assert isinstance(result, str)
    assert result == expected


def test_str_field_adds_max_length_validator():
    validators = StrField(max_length=10).validators
    assert len(validators) == 3
    assert isinstance(validators[2], avocato_validators.Length)
    assert validators[2].max_length == 10


def test_str_field_adds_min_length_validator():
    validators = StrField(min_length=10).validators
    assert len(validators) == 3
    assert isinstance(validators[2], avocato_validators.Length)
    assert validators[2].min_length == 10


def test_str_field_adds_one_of_validator_if_choices_are_set():
    validators = StrField(choices=['a', 'b']).validators
    assert len(validators) == 3
    assert isinstance(validators[2], avocato_validators.OneOf)
    assert validators[2].choices == ['a', 'b']


@pytest.mark.parametrize('value,expected', [
    (5, '5',),
    ('abrakadabra@omg.com', 'abrakadabra@omg.com',),
    (None, 'None',),
])
def test_email_field_to_value_returns_str(value, expected):
    result = EmailField().to_value(value)
    assert isinstance(result, str)
    assert result == expected


def test_email_field_adds_email_validator():
    validators = EmailField().validators
    assert len(validators) == 3
    assert isinstance(validators[2], avocato_validators.Email)


def test_email_subclasses_str_field():
    assert isinstance(EmailField(), StrField)


@pytest.mark.parametrize('value,expected', [
    ('5', 5,),
    (5, 5,),
    (5.5, 5,),
    (Decimal('5.555'), 5)
])
def test_int_field_to_value_returns_int(value, expected):
    result = IntField().to_value(value)
    assert isinstance(result, int)
    assert result == expected


@pytest.mark.parametrize('value,expected', [
    ('5', 5.0,),
    (5, 5.0,),
    (5.5, 5.5,),
    (Decimal('5.555'), 5.555)
])
def test_float_field_to_value_returns_float(value, expected):
    result = FloatField().to_value(value)
    assert isinstance(result, float)
    assert result == expected


@pytest.mark.parametrize('value,expected', [
    ('5', True,),
    ('', False,),
    (5, True,),
    (1, True),
    (True, True),
    (False, False)
])
def test_bool_field_to_value_returns_bool(value, expected):
    result = BoolField().to_value(value)
    assert isinstance(result, bool)
    assert result == expected


@pytest.mark.parametrize('value,expected', [
    ('5', '5',),
    (5, '5',),
    (5.5, '5.5',),
    (Decimal('5.555'), '5.555')
])
def test_decimal_field_to_value_returns_str(value, expected):
    result = DecimalField().to_value(value)
    assert isinstance(result, str)
    assert result == expected


def test_datetime_field_to_value_returns_date_in_iso_format():
    result = DateTimeField().to_value(datetime(2019, 1, 8, 13, 37))
    assert isinstance(result, str)
    assert result == '2019-01-08T13:37:00'


def test_dict_field_to_value_returns_dict():
    result = DictField().to_value({'foo': 'bar'})
    assert isinstance(result, dict)
    assert result == {'foo': 'bar'}


def test_method_field():
    class MethodSerializer(object):
        def get_foo(self):
            return 'bar'

    serializer = MethodSerializer()
    field = MethodField(attr='foo')
    assert field.as_getter('foo', serializer)() == 'bar'
