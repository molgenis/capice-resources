from enum import Enum


class ThresholdEnums(Enum):
    """
    Enums specific to the Threshold calculator.
    """
    CALCULATED_THRESHOLD = 'calculated_threshold'
    RECALL = 'Recall_score'
    INRANGE = 'in_range'
    THRESHOLD = 'Threshold'
    PRECISION = 'Precision'
    F1 = 'F1_score'
    THRESHOLDS = 'thresholds'
    FIGURE = 'figure'
