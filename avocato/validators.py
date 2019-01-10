import re

from .exceptions import AvocatoValidationError


class Validator(object):
    """Base class for validators.
    """
    def __repr__(self):
        args = self._repr_args()
        args = '{0}, '.format(args) if args else ''

        return (
            '<{self.__class__.__name__}({args}message={self.message!r})>'
            .format(self=self, args=args)
        )

    def _repr_args(self):
        return ''


class Required(Validator):
    """Validates if value is set.

    Raises exception if value is empty or None
    """
    default_message = 'This field is required'

    def __init__(self, message=None):
        self.message = message or self.default_message

    def _format_error(self, value):
        return self.message

    def __call__(self, value):
        if not value:
            raise AvocatoValidationError(self._format_error(value))
        return value


class Email(Validator):
    """Validates if value is in valid email format
    """
    USER_REGEX = re.compile(
        r"(^[-!#$%&'*+/=?^`{}|~\w]+(\.[-!#$%&'*+/=?^`{}|~\w]+)*$"
        r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]'
        r'|\\[\001-\011\013\014\016-\177])*"$)', re.IGNORECASE | re.UNICODE,
    )

    DOMAIN_REGEX = re.compile(
        # domain
        r'(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+'
        r'(?:[A-Z]{2,6}|[A-Z0-9-]{2,})$'
        # literal form, ipv4 address (SMTP 4.1.3)
        r'|^\[(25[0-5]|2[0-4]\d|[0-1]?\d?\d)'
        r'(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}\]$', re.IGNORECASE | re.UNICODE,
    )

    default_message = 'Not a valid email address.'

    def __init__(self, message=None):
        self.message = message

    def _format_error(self, value):
        return (self.message or self.default_message).format(input=value)

    def __call__(self, value):
        message = self._format_error(value)

        if not value or '@' not in value:
            raise AvocatoValidationError(message)

        user_part, domain_part = value.rsplit('@', 1)

        if not self.USER_REGEX.match(user_part):
            raise AvocatoValidationError(message)

        if not self.DOMAIN_REGEX.match(domain_part):
            try:
                domain_part = domain_part.encode('idna').decode('ascii')
            except UnicodeError:
                pass
            else:
                if self.DOMAIN_REGEX.match(domain_part):
                    return value
            raise AvocatoValidationError(message)

        return value


class Length(Validator):
    """Validates if value is correct size.
    """
    message_min = 'Shorter than minimum length {min_length}.'
    message_max = 'Longer than maximum length {max_length}.'
    message_all = 'Length must be between {min_length} and {max_length}.'
    message_equal = 'Length must be {equal}.'

    def __init__(self, min_length=None, max_length=None, message=None, equal=None):
        if equal is not None and any([min_length, max_length]):
            raise ValueError(
                'The `equal` parameter was provided, maximum or '
                'minimum parameter must not be provided.',
            )

        self.min_length = min_length
        self.max_length = max_length
        self.message = message
        self.equal = equal

    def _repr_args(self):
        return 'min_length={0!r}, max_length={1!r}, equal={2!r}'.format(
            self.min_length, self.max, self.equal)

    def _format_error(self, value, message):
        return (self.message or message).format(
            input=value, min_length=self.min_length, max_length=self.max_length,
            equal=self.equal,
        )

    def __call__(self, value):
        length = len(value)

        if self.equal is not None:
            if length != self.equal:
                raise AvocatoValidationError(self._format_error(value, self.message_equal))
            return value

        if self.min_length is not None and length < self.min_length:
            message = self.message_min if self.max_length is None else self.message_all
            raise AvocatoValidationError(self._format_error(value, message))

        if self.max_length is not None and length > self.max_length:
            message = self.message_max if self.min_length is None else self.message_all
            raise AvocatoValidationError(self._format_error(value, message))

        return value


class OneOf(Validator):
    """Validates if the value is one of the choices.
    """
    default_message = 'Value {input} must be one of {choices}.'

    def __init__(self, choices, message=None):
        self.choices = choices
        self.choices_text = ', '.join(str(choice) for choice in self.choices)
        self.message = message or self.default_message

    def _repr_args(self):
        return 'choices={0!r}'.format(self.choices)

    def _format_error(self, value):
        return self.message.format(
            input=value,
            choices=self.choices_text,
        )

    def __call__(self, value):
        try:
            if value not in self.choices:
                raise AvocatoValidationError(self._format_error(value))
        except TypeError:
            raise AvocatoValidationError(self._format_error(value))

        return value


class OneOfType(Validator):
    """Validates if value type is one of the choices.
    """
    default_message = 'Value {input} of type {input_type} must be one of {choices} type'

    def __init__(self, choices, message=None):
        self.choices = choices
        self.choices_text = ', '.join(str(choice) for choice in self.choices)
        self.message = message or self.default_message

    def _repr_args(self):
        return 'choices={0!r}'.format(self.choices)

    def _format_error(self, value):
        return self.message.format(
            input=value,
            input_type=type(value),
            choices=self.choices_text,
        )

    def __call__(self, value):
        if not isinstance(value, self.choices):
            raise AvocatoValidationError(self._format_error(value))
        return value
