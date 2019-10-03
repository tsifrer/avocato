import pytest

from avocato import validators as avocato_validators
from avocato.fields import EmailField, Field, MethodField, StrField


@pytest.mark.parametrize("value,expected", [(5, 5), ("a", "a"), (None, None)])
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
    validators = StrField(choices=["a", "b"]).validators
    assert len(validators) == 3
    assert isinstance(validators[2], avocato_validators.OneOf)
    assert validators[2].choices == ["a", "b"]


def test_email_field_adds_email_validator():
    validators = EmailField().validators
    assert len(validators) == 3
    assert isinstance(validators[2], avocato_validators.Email)


def test_email_subclasses_str_field():
    assert isinstance(EmailField(), StrField)


def test_method_field():
    class MethodSerializer(object):
        def get_foo(self):
            return "bar"

    serializer = MethodSerializer()
    field = MethodField(attr="foo")
    assert field.as_getter("foo", serializer)() == "bar"
