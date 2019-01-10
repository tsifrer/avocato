
class AvocatoError(Exception):
    """Base avocato exception.
    """


class AvocatoValidationError(AvocatoError):
    """Exception used for validating values.
    """
    def __init__(self, message, field_names=None, data=None, valid_data=None, **kwargs):
        if not isinstance(message, dict) and not isinstance(message, list):
            self.messages = [message]
        else:
            self.messages = message

        if isinstance(field_names, str):
            self.field_names = [field_names]
        else:
            self.field_names = field_names or []

        self.data = data
        self.valid_data = valid_data
        self.kwargs = kwargs
        AvocatoError.__init__(self, message)
