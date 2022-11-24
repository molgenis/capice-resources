from enum import Enum


class ExtendedEnum(Enum):
    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))


class RequiredValidationColumns(ExtendedEnum):
    BINARIZED_LABEL = 'binarized_label'


class RequiredScoreColumns(ExtendedEnum):
    SCORE = 'score'
