import typing


class IsInstanceOf:
    def __init__(self, expected_type: type):
        self.expected_type = expected_type

    def __eq__(self, other: typing.Any) -> bool:  # noqa: ANN401
        return isinstance(other, self.expected_type)
