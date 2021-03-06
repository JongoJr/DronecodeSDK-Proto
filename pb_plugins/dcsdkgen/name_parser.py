import re


class NameParser:

    def __init__(self, name):
        self._name = name

    @property
    def uppercase(self):
        return self._name.upper()

    @property
    def lowercase(self):
        return self._name.lower()

    @property
    def upper_camel_case(self):
        return self._name

    @property
    def lower_camel_case(self):
        return self._name[0].lower() + self._name[1:] if self._name else ""

    @property
    def upper_snake_case(self):
        return re.sub('(?<!^)(?=[A-Z])',
                      '_',
                      self._name)

    @property
    def lower_snake_case(self):
        return self.upper_snake_case.lower()
