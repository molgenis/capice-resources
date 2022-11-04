from enum import Enum


class ExtendedEnum(Enum):
    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))


class ValidationColumns(ExtendedEnum):
    BINARIZED_LABEL = 'binarized_label'


class ScoreColumns(ExtendedEnum):
    SCORE = 'score'
