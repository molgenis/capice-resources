import os
from pathlib import Path

import pandas as pd

from molgenis.capice_resources.utilities import add_dataset_source
from molgenis.capice_resources.core import Module, TSVFileEnums, DatasetIdentifierEnums, \
    ColumnEnums, VCFEnums
from molgenis.capice_resources.core.errors import SampleSizeMismatchError
from molgenis.capice_resources.compare_model_performance.plotter import Plotter
from molgenis.capice_resources.compare_model_performance.annotator import Annotator
from molgenis.capice_resources.compare_model_performance import CompareModelPerformanceEnums as \
    Menums
from molgenis.capice_resources.compare_model_performance.consequence_tools import ConsequenceTools


class CompareModelPerformance(Module):
    def __init__(self):
        super().__init__(
            program='Compare model performance',
            description='Compares the performance of 2 different XGBoost style models. '
                        'Please note that model 1 is leading for '
                        'the per-consequence performance measurements. '
                        'If the size of the label file does not match the size of the scores file, '
                        'an attempt will be made to map the labels to the '
                        'scores through the use of the columns: '
                        '`CHROM`, `POS`, `REF`, `ALT` and `SYMBOL`. '
                        'Will error if one of these columns is missing in either '
                        'the score file or the label file, assuming sizes differ.'
        )

    @staticmethod
    def _create_module_specific_arguments(parser):
        required = parser.add_argument_group('Required arguments')
        optional = parser.add_argument_group('Optional arguments')

        required.add_argument(
            '-a',
            '--scores-model-1',
            type=str,
            required=True,
            help='Input location of the file containing the scores for model 1. '
                 'Column `Consequence` is required to be present in either the score file or '
                 'the label file (or both). '
                 'Has to contain the `score` column and '
                 'must be supplied in either TSV or gzipped TSV format! '
                 'Leading for per-consequence performance metrics.'
        )

        required.add_argument(
            '-l',
            '--labels',
            '--labels-model-1',
            type=str,
            required=True,
            help='Input location of the validation file used to create the score files. '
                 'If 2 seperate validation files are used, this argument is for the validation '
                 'file used to generate -a/--scores-model-1. '
                 'Column `Consequence` is required to be present in either the score file or '
                 'the label file (or both). '
                 'Has to contain the `binarized_label` column and '
                 'must be supplied in either TSV or gzipped TSV format! '
                 'Leading for per-consequence performance metrics.'
        )

        required.add_argument(
            '-b',
            '--scores-model-2',
            type=str,
            required=True,
            help='Input location of the file containing the scores for model 2. '
                 'Column `Consequence` is required to be present in either the score file or '
                 'the label file (or both). '
                 'Has to contain the `score` column and '
                 'must be supplied in either TSV or gzipped TSV format!'
        )

        optional.add_argument(
            '-m',
            '--labels-model-2',
            type=str,
            help='Optional input location of the file containing the labels for model 2. '
                 'Must be supplied in either TSV or gzipped TSV format! '
                 'If not defined, uses file given through -l/--labels/--labels-model-1 for model 2.'
        )

        required.add_argument(
            '-o',
            '--output',
            type=str,
            required=True,
            help='Output directory.'
        )

        optional.add_argument(
            '-f',
            '--force-merge',
            action='store_true',
            help='Add flag if there is a possibility of a mismatch in sample size between the '
                 'score and label file for any model.'
        )

        return parser

    def _validate_module_specific_arguments(self, parser):
        scores1 = self.input_validator.validate_input_command_line_interface_file(
            parser.get_argument('scores_model_1'),
            TSVFileEnums.TSV_EXTENSIONS.value
        )
        scores2 = self.input_validator.validate_input_command_line_interface_file(
            parser.get_argument('scores_model_2'),
            TSVFileEnums.TSV_EXTENSIONS.value
        )
        labels = self.input_validator.validate_input_command_line_interface_file(
            parser.get_argument('labels'),
            TSVFileEnums.TSV_EXTENSIONS.value
        )
        labels_2 = self.input_validator.validate_input_command_line_interface_file(
            parser.get_argument('labels_model_2'),
            TSVFileEnums.TSV_EXTENSIONS.value,
            can_be_optional=True
        )
        output = self.input_validator.validate_output_command_line_interface_path(
            parser.get_argument('output')
        )
        force_merge = parser.get_argument('force_merge')
        return {
            **scores1,
            **scores2,
            **labels,
            **labels_2,
            **output,
            **force_merge
        }

    def run_module(self, arguments):
        path_scores_model_1 = arguments['scores_model_1']
        path_labels_model_1 = arguments['labels']
        path_scores_model_2 = arguments['scores_model_2']
        path_labels_model_2 = arguments['labels_model_2']

        model_1, model_2 = self._read_and_parse_input_data(
            path_scores_model_1,
            path_labels_model_1,
            path_scores_model_2,
            path_labels_model_2,
            arguments['force_merge']
        )
        consequence_tools = ConsequenceTools()
        consequences = consequence_tools.has_consequence(model_1, model_2)
        if consequences:
            consequence_tools.validate_consequence_samples_equal(
                model_1,
                model_2,
                consequences
            )

        annotator = Annotator()
        annotator.add_score_difference(model_1)
        annotator.add_score_difference(model_2)

        annotator.add_and_process_impute_af(model_1)
        annotator.add_and_process_impute_af(model_2)

        add_dataset_source(model_1, Menums.MODEL_1.value)
        add_dataset_source(model_2, Menums.MODEL_2.value)

        plotter = Plotter(
            consequences,
            path_scores_model_1,
            path_labels_model_1,
            path_scores_model_2,
            path_labels_model_2
        )
        plots = plotter.plot(model_1, model_2)
        return {**plots, DatasetIdentifierEnums.OUTPUT.value: arguments['output']}

    def _read_and_parse_input_data(
            self,
            scores1_argument: os.PathLike | Path | str,
            labels1_argument: os.PathLike | Path | str,
            scores2_argument: os.PathLike | Path | str,
            labels2_argument: os.PathLike | Path | str | None,
            force_merge_argument: bool
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Function to read and parse the scores and labels arguments.

        Args:
            scores1_argument:
                Path to the score file of model 1.
            labels1_argument:
                Path to the label file (of model 2).
            scores2_argument:
                Path to the score file of model 2.
            labels2_argument:
                Optional argument of the label file of model 2 if supplied through CLI.
            force_merge_argument:
                Boolean flag if scores and labels should be force merged if the sizes differ.

        Returns:
            tuple:
                Tuple containing [0]: the merged frame for model 1 and [1] the merged frame for
                model 2.
        """
        scores_model_1 = self._read_pandas_tsv(
            scores1_argument,
            [  # type: ignore
                ColumnEnums.SCORE.value
            ]
        )
        scores_model_2 = self._read_pandas_tsv(
            scores2_argument,
            [  # type: ignore
                ColumnEnums.SCORE.value
            ]
        )
        labels = self._read_pandas_tsv(
            labels1_argument,
            [  # type: ignore
                ColumnEnums.BINARIZED_LABEL.value,
                ColumnEnums.GNOMAD_AF.value
            ]
        )
        # No _read_pandas_tsv yet, since it can be None
        labels2 = labels2_argument
        force_merge = force_merge_argument
        merge_model_1 = self._merge_scores_and_labes(
            scores_model_1,
            labels,
            force_merge  # type: ignore
        )
        if labels2 is None:
            merge_model_2 = self._merge_scores_and_labes(
                scores_model_2,
                labels,
                force_merge  # type: ignore
            )
        else:
            labels_model_2 = self._read_pandas_tsv(
                labels2,
                [  # type: ignore
                    ColumnEnums.BINARIZED_LABEL.value,
                    ColumnEnums.GNOMAD_AF.value
                ]
            )
            merge_model_2 = self._merge_scores_and_labes(
                scores_model_2,
                labels_model_2,
                force_merge  # type: ignore
            )
        return merge_model_1, merge_model_2

    def _merge_scores_and_labes(
            self,
            scores: pd.DataFrame,
            labels: pd.DataFrame,
            force_merge: bool
    ) -> pd.DataFrame:
        """
        Function to perform the merge of scores and labels.

        Args:
            scores:
                The pandas frame containing the CAPICE scores.
            labels:
                The pandas frame containing the labels / binarized_labels.
            force_merge:
                The boolean flag if a force merge should be attempted in case sample sizes mismatch.

        Returns:
            dataframe:
                Merged frame between scores and labels. Please note that if force_merge is used,
                the "scores" is leading in the merging.

        Raises:
            SampleSizeMismatchError:
                SampleSizeMismatchError is raised when force_merge is set to False and the sample
                sizes differ.
        """
        if scores.shape[0] == labels.shape[0]:
            merge = pd.concat([scores, labels], axis=1)
        else:
            merge = self._attempt_mismatch_merge(scores, labels, force_merge)
        return merge

    def _attempt_mismatch_merge(
            self,
            scores: pd.DataFrame,
            labels: pd.DataFrame,
            force_merge:  bool
    ) -> pd.DataFrame:
        """
        Function to attempt the merge between scores and labels in case sample sizes differ.

        Args:
            scores:
                The frame containing the CAPICE scores.
            labels:
                The frame containing the labels / binarized_labels.
            force_merge:
                Boolean if the merge should be attempted or an error should be raised.

        Returns:
            merge:
                Merged frame of scores and labels that have different sample sizes. Scores is
                leading in the merge.

        Raises:
            SampleSizeMismatchError:
                SampleSizeMismatchError is raised when force_merge is set to False and the sample
                sizes differ.
        """
        if not force_merge:
            raise SampleSizeMismatchError(
                'Sample sizes differ and -f/--force-merge is not supplied!'
            )
        scores_merge_columns = [
            VCFEnums.CHROM.shortened_name,
            VCFEnums.POS.lower,
            VCFEnums.REF.lower,
            VCFEnums.ALT.lower,
            Menums.GENE_NAME.value
        ]
        self.data_validator.validate_pandas_dataframe(
            scores,
            scores_merge_columns
        )
        labels_merge_columns = [
            VCFEnums.CHROM.processed_name,
            VCFEnums.POS.value,
            VCFEnums.REF.value,
            VCFEnums.ALT.value,
            ColumnEnums.SYMBOL.value
        ]
        self.data_validator.validate_pandas_dataframe(
            labels,
            labels_merge_columns
        )
        scores[Menums.MERGE_COLUMN.value] = scores[scores_merge_columns].astype(
            str).agg(VCFEnums.ID_SEPARATOR.value.join, axis=1)
        labels[Menums.MERGE_COLUMN.value] = labels[labels_merge_columns].astype(
            str).agg(VCFEnums.ID_SEPARATOR.value.join, axis=1)
        return scores.merge(labels, on=Menums.MERGE_COLUMN.value, how='left')  # type: ignore

    def export(self, output) -> None:
        output_path = output[DatasetIdentifierEnums.OUTPUT.value]
        for filename, figure in output.items():
            if filename == DatasetIdentifierEnums.OUTPUT.value:
                continue
            figure.savefig(os.path.join(output_path, filename + '.png'))  # type: ignore


def main():
    CompareModelPerformance().run()


if __name__ == '__main__':
    main()
