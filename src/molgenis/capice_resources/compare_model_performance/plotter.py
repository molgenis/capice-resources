import math
import os

import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt
from matplotlib import patches as mpatches


from molgenis.capice_resources.core import ColumnEnums, PlottingEnums, AlleleFrequencyEnums
from molgenis.capice_resources.compare_model_performance import CMPPlottingEnums
from molgenis.capice_resources.compare_model_performance.consequence_tools import ConsequenceTools
from molgenis.capice_resources.compare_model_performance.performance_calculator import \
    PerformanceCalculator
from molgenis.capice_resources.compare_model_performance import CompareModelPerformanceEnums


class Plotter:
    def __init__(
            self,
            process_consequences: list[str] | bool,
            model_1_score_path: os.PathLike,
            model_1_label_path: os.PathLike,
            model_2_score_path: os.PathLike,
            model_2_label_path: os.PathLike | None,
    ):
        """
        Init of the Plotter class.
        Sets all the figurines and globally accessible variables.

        Args:
            process_consequences:
                The list (or False) of all the unique and split consequences.
            model_1_score_path:
                The path to the model 1 score file.
            model_1_label_path:
                The path to the model 1 label file.
            model_2_score_path:
                The path to the model 2 score file.
            model_2_label_path:
                (Optional) The path to the model 2 label file.
        """
        self.calculator = PerformanceCalculator()
        self.process_consequences = process_consequences
        self.index = 1
        self.fig_auc = plt.figure()
        self.fig_roc = plt.figure()
        self.fig_afb = plt.figure()
        self.fig_score_dist_box = plt.figure()
        self.fig_score_dist_vio = plt.figure()
        self.fig_score_diff_box = plt.figure()
        self.fig_score_diff_vio = plt.figure()
        self._prepare_figure_supertitle_and_size(
            model_1_score_path,
            model_1_label_path,
            model_2_score_path,
            model_2_label_path
        )
        self.n_rows = 1
        self.n_cols = 1
        self._set_nrows_and_ncols()

    @staticmethod
    def _set_figure_size(process_consequences: list[str] | bool) -> tuple[int, int]:
        """
        Depending on if process_consequences is true or not, set the figures to a greater size.

        Args:
            process_consequences:
                List or False of all the unique and split consequences.

        Returns:
            tuple:
                Tuple containing [0] the image width and [1] the image length. If
                process_consequences is a list, will return (20, 40) (which means 2000 pixels
                wide and 4000 pixels tall). If False: (10,15).
        """
        if process_consequences:
            return 20, 40
        else:
            return 10, 15

    def _prepare_figure_supertitle_and_size(
            self,
            model_1_score_path,
            model_1_label_path,
            model_2_score_path,
            model_2_label_path
    ) -> None:
        """
        Preparatory function to set the super title and image size to each of the figures.

        Args:
            model_1_score_path:
                The path to the model 1 score file.
            model_1_label_path:
                The path to the model 1 label file.
            model_2_score_path:
                The path to the model 2 score file.
            model_2_label_path:
                (Optional) The path to the model 2 label file.
        """
        print('Preparing plot figures.')
        figsize = self._set_figure_size(self.process_consequences)
        print('Preparing plots.')

        if model_2_label_path is None:
            model_2_label_path = model_1_label_path

        figure_supertitle = f'Model 1 scores: {model_1_score_path}\n' \
                            f'Model 1 labels: {model_1_label_path}\n' \
                            f'Model 2 scores: {model_2_score_path}\n' \
                            f'Model 2 labels: {model_2_label_path}\n'

        self._set_size_supertitle_layout(
            self.fig_auc,
            f'Area Under Receiver Operator Curve\n{figure_supertitle}',
            figsize
        )

        self._set_size_supertitle_layout(
            self.fig_roc,
            f'Receiver Operator Curves\n{figure_supertitle}',
            (10, 15)
        )

        self._set_size_supertitle_layout(
            self.fig_afb,
            f'Allele Frequency bins performance comparison\n{figure_supertitle}',
            (11, 11)
        )

        self._set_size_supertitle_layout(
            self.fig_score_dist_box,
            f'raw CAPICE score distribution box plots\n{figure_supertitle}',
            figsize
        )

        self._set_size_supertitle_layout(
            self.fig_score_dist_vio,
            f'raw CAPICE score distribution violin plots\n{figure_supertitle}',
            figsize
        )

        self._set_size_supertitle_layout(
            self.fig_score_diff_box,
            f'absolute score differences to the true label box plots\n{figure_supertitle}',
            figsize
        )

        self._set_size_supertitle_layout(
            self.fig_score_diff_vio,
            f'absolute score differences to the true label violin plots\n{figure_supertitle}',
            figsize
        )

        print('Plot figures prepared.\n')

    @staticmethod
    def _set_size_supertitle_layout(
            figure: plt.Figure,
            figure_supertitle: str,
            figure_size: tuple[int, int]
    ) -> None:
        """
        Prepares a matplotlib.pyplot.Figure supertitle, width, height and sets the constrained
        layout of "w_pad" and "h_pad" to 0.2.

        Args:
            figure:
                the matplotlib.pyplot.Figure to be prepared.
            figure_supertitle:
                single string of the complete figure supertitle, containing the
                type of the plot (AUC/ROC/score distributions etc.) followed by all
                the model paths and maybe a post_supertitle for the boxplots.
                Does NOT format the string!
            figure_size:
                tuple containing the [0] figure width and [1] figure height.
        """
        figure.set_dpi(PlottingEnums.DPI.value)
        figure.set_figwidth(figure_size[0])
        figure.set_figheight(figure_size[1])
        figure.suptitle(
            f'Model 1 vs Model 2 {figure_supertitle}'
        )
        figure.set_constrained_layout(PlottingEnums.CONSTRAINED_LAYOUT.value)

    def _set_nrows_and_ncols(self) -> None:
        """
        Preparatory function to set the amount of rows and columns in a multi plot figure.

        If consequences are present sets the amount of columns to 3 and the amount of rows to
        the amount of consequences divided by the amount of columns (3). To prevent that rows
        is going to be a float, it is rounded up to prevent consequences not ending up on
        the figure.

        """
        if self.process_consequences:
            print(
                'Creating required amount of rows and columns according to present Consequences.\n'
            )
            self.n_cols = 3
            self.n_rows = math.ceil(
                (len(self.process_consequences) / self.n_cols + 1)  # type: ignore
            )
        else:
            print('Creating single plot per figure.\n')

    def plot(
            self,
            merged_model_1_data: pd.DataFrame,
            merged_model_2_data: pd.DataFrame
    ) -> dict[str, plt.Figure]:
        """
        Main function of the plotter class.

        Args:
            merged_model_1_data:
                Merged frame of the model 1 data. Contains both the score and labels frames.
            merged_model_2_data:
                Merged frame of the model 2 data. Contains both the score and labels frames.

        Returns:
            dict:
                Dictionary containing [key] figure name and [value] the figure itself.
        """
        m1_samples = merged_model_1_data.shape[0]
        m2_samples = merged_model_2_data.shape[0]

        print('Plotting global ROC, AUC, AF Bins, Score distributions and Score differences.')
        self._plot_roc_auc_afbins(merged_model_1_data, m1_samples, merged_model_2_data, m2_samples)
        self._plot_score_dist(merged_model_1_data, m1_samples, merged_model_2_data, m2_samples,
                              CMPPlottingEnums.GLOBAL.value)
        self._plot_score_diff(merged_model_1_data, m1_samples, merged_model_2_data, m2_samples,
                              CMPPlottingEnums.GLOBAL.value)
        print('Plotting globally done.\n')
        if self.process_consequences:
            print('Plotting per consequence.')
            self.index += 1
            self._plot_consequences(merged_model_1_data, merged_model_2_data)
            print('Plotting per consequence done.\n')

        return {
            CMPPlottingEnums.FIG_ROC.value: self.fig_roc,
            CMPPlottingEnums.FIG_AUC.value: self.fig_auc,
            CMPPlottingEnums.FIG_AF.value: self.fig_afb,
            CMPPlottingEnums.FIG_B_DIST.value: self.fig_score_dist_box,
            CMPPlottingEnums.FIG_V_DIST.value: self.fig_score_dist_vio,
            CMPPlottingEnums.FIG_B_DIFF.value: self.fig_score_diff_box,
            CMPPlottingEnums.FIG_V_DIFF.value: self.fig_score_diff_vio
        }

    def _plot_roc_auc_afbins(
            self,
            model_1_data: pd.DataFrame,
            model_1_size: int,
            model_2_data: pd.DataFrame,
            model_2_size: int
    ) -> None:
        """
        Function to house the calls to the ROC, AUC and Allele Frequency bin plotters for global
        performance.

        Args:
            model_1_data:
                The dataframe of the score and label data of model 1.
            model_1_size:
                The amount of samples in model_1_data.
            model_2_data:
                The dataframe of the score and label data of model 2.
            model_2_size:
                The amount of samples in model_2_data.

        """
        fpr_m1, tpr_m1, auc_m1 = self.calculator.calculate_roc(model_1_data)
        fpr_m2, tpr_m2, auc_m2 = self.calculator.calculate_roc(model_2_data)
        self._plot_roc(fpr_m1, tpr_m1, auc_m1, fpr_m2, tpr_m2, auc_m2)
        self._plot_auc(auc_m1, model_1_size, auc_m2, model_2_size, CMPPlottingEnums.GLOBAL.value)
        self._plot_af_bins(model_1_data, model_2_data)

    def _plot_consequences(
            self,
            merged_model_1_data: pd.DataFrame,
            merged_model_2_data: pd.DataFrame
    ) -> None:
        """
        Function to call each of the plotters on a per consequence base.

        Args:
            merged_model_1_data:
                Merged frame of the data of model 1, containing the score and labels.
            merged_model_2_data:
                Merged frame of the data of model 2, containing the score and labels.

        """
        consequence_tools = ConsequenceTools()
        for consequence in self.process_consequences:  # type: ignore
            subset_m1 = consequence_tools.subset_consequence(merged_model_1_data, consequence)
            m1_samples = subset_m1.shape[0]
            subset_m2 = consequence_tools.subset_consequence(merged_model_2_data, consequence)
            m2_samples = subset_m2.shape[0]
            try:
                auc_m1 = self.calculator.calculate_auc(subset_m1)
                auc_m2 = self.calculator.calculate_auc(subset_m2)
            except ValueError:
                auc_m1 = np.NaN
                auc_m2 = np.NaN

            self._plot_auc(auc_m1, m1_samples, auc_m2, m2_samples, consequence)
            self._plot_score_dist(subset_m1, m1_samples, subset_m2, m2_samples, consequence)
            self._plot_score_diff(subset_m1, m1_samples, subset_m2, m2_samples, consequence)
            self.index += 1

    def _plot_roc(
            self,
            fpr_model_1: np.ndarray,
            tpr_model_1: np.ndarray,
            auc_model_1: float,
            fpr_model_2: np.ndarray,
            tpr_model_2: np.ndarray,
            auc_model_2: float
    ) -> None:
        """
        Plotter method for specifically the Receiver Operator Curve plot.

        Args:
            fpr_model_1:
                Float of the False Positive Rate of model 1.
            tpr_model_1:
                Float of the True Positive Rate of model 1.
            auc_model_1:
                Float of the Area Under Curve of model 1.
            fpr_model_2:
                Float of the False Positive Rate of model 2.
            tpr_model_2:
                Float of the True Positive Rate of model 2.
            auc_model_2:
                Float of the False Positive Rate of model 2.
        """
        # Plotting ROCs
        ax_roc = self.fig_roc.add_subplot(1, 1, 1)
        ax_roc.plot(fpr_model_1, tpr_model_1, color='red', label=f'Model 1 (AUC={auc_model_1})')
        ax_roc.plot(fpr_model_2, tpr_model_2, color='blue', label=f'Model 2 (AUC={auc_model_2})')
        ax_roc.plot([0, 1], [0, 1], color='black', linestyle='--')
        ax_roc.set_xlim([0.0, 1.0])
        ax_roc.set_ylim([0.0, 1.0])
        ax_roc.set_xlabel('False Positive Rate')
        ax_roc.set_ylabel('True Positive Rate')
        ax_roc.legend(loc='lower right')

    @staticmethod
    def _create_af_bins_plotlabels(
            bin_label: str,
            model_1_size: int,
            model_1_auc: float,
            model_2_size: int,
            model_2_auc: float
    ) -> str:
        """
        Creates a label specifically for the allele frequency bins

        Returns single string:
            If sample sizes match:
                {bin_label}
                Model 1: {auc}
                Model 2: {auc}
                {sample_size}
                {\n}

            If not:
                {bin_label}
                Model 1: {auc} (n: {sample_size})
                Model 2: {auc} (n: {sample_size})
                {\n}
        """
        if model_1_size == model_2_size:
            return f'{bin_label}\nModel 1: {model_1_auc}\nModel 2: {model_2_auc}\nn: {model_1_size}'
        else:
            return f'{bin_label}\nModel 1: {model_1_auc} (n: {model_1_size})\n' \
                   f'Model 2: {model_2_auc} (n: {model_2_size})'

    @staticmethod
    def _subset_af_bin(
            dataset: pd.DataFrame,
            upper_bound: float | int,
            lower_bound: float | int,
            last_iter: bool = False
    ) -> pd.DataFrame:
        """
        Function to subset "dataset" based upon the upper_bound and lower_bound.
        Last_iter is to prevent that the last iteration includes the upper bound.

        Args:
            dataset:
                The dataframe that should be subset upon.
            upper_bound:
                The lower bound that the subset should start from (and include).
            lower_bound:
                The lower bound that the subset should start from (and include, except when
                last_iter is set to True).
            last_iter:
                Boolean True if the last iteration on the allele frequency bins has been reached.
        Returns:
            subset:
                Subset of "dataset" that only contains samples between upper bound and lower
                bound allele frequencies.
        """
        if last_iter:
            return dataset[
                (dataset[ColumnEnums.GNOMAD_AF.value] >= lower_bound) &
                (dataset[ColumnEnums.GNOMAD_AF.value] <= upper_bound) &
                (~dataset[ColumnEnums.IMPUTED.value])
                ]
        else:
            return dataset[
                (dataset[ColumnEnums.GNOMAD_AF.value] >= lower_bound) &
                (dataset[ColumnEnums.GNOMAD_AF.value] < upper_bound) &
                (~dataset[ColumnEnums.IMPUTED.value])
                ]

    def _plot_bin(
            self,
            ax: plt.Axes,
            x_index: int,
            label: str,
            auc_m1: float,
            m1_ss: int,
            auc_m2: float,
            m2_ss: int
    ) -> None:
        """
        Plotter function of the plot allele frequencies function.

        Args:
            ax:
                The matplotlib Axes object to plot the plot on.
            x_index:
                The x-index on which the bars should be placed.
            label:
                The label the bars should get.
            auc_m1:
                The AUC of model 1.
            m1_ss:
                The sample size of model 1.
            auc_m2:
                The AUC of model 2.
            m2_ss:
                The sample size of model 2.

        """
        width = 0.3
        ax.bar(
            x_index - width,
            auc_m1,
            width,
            align='edge',
            color='red'
        )
        ax.bar(
            x_index,
            auc_m2,
            width,
            align='edge',
            color='blue'
        )
        ax.plot(
            np.NaN,
            np.NaN,
            color='none',
            label=self._create_af_bins_plotlabels(
                label,
                m1_ss,
                auc_m1,
                m2_ss,
                auc_m2
            )
        )

    def _plot_af_bins(
            self,
            model_1_data: pd.DataFrame,
            model_2_data: pd.DataFrame
    ) -> None:
        """
        Main function of the Allele Frequency plotting capability.
        Loops through the AF bins and calls the plotter function for each bin.
        Adds the plots to the AF bins figure.

        Args:
            model_1_data:
                Merged frame of the data of model 1, containing the score and labels.
            model_2_data:
                Merged frame of the data of model 2, containing the score and labels.

        """
        ax_afb = self.fig_afb.add_subplot(1, 1, 1)
        bin_labels = []

        # Plotting the NaN AF values as if they were singletons
        # Including imputed and non-imputed 0
        try:
            f_auc_m1 = self.calculator.calculate_auc(
                model_1_data[model_1_data[ColumnEnums.GNOMAD_AF.value] == 0]
            )
            f_auc_m2 = self.calculator.calculate_auc(
                model_2_data[model_2_data[ColumnEnums.GNOMAD_AF.value] == 0]
            )
        except ValueError:
            print('Could not calculate an AUC for possible singleton variants.')
            f_auc_m1 = np.NaN
            f_auc_m2 = np.NaN
        bin_labels.append('"0"')

        self._plot_bin(
            ax_afb,
            0,
            '"0"',
            f_auc_m1,
            model_1_data[model_1_data[ColumnEnums.GNOMAD_AF.value] == 0].shape[0],
            f_auc_m2,
            model_2_data[model_2_data[ColumnEnums.GNOMAD_AF.value] == 0].shape[0]
        )

        bins = AlleleFrequencyEnums.AF_BINS.value
        # Sadly bins*100 doesn't work for 1e-6, cause of rounding errors
        bins_labels = [0, 1e-4, 1e-3, 0.01, 0.1, 1, 100]
        for i in range(1, len(bins)):
            last_iter = False
            upper_bound = bins[i]
            if upper_bound == bins[-1]:
                last_iter = True
            lower_bound = bins[i - 1]
            subset_m1 = self._subset_af_bin(model_1_data, upper_bound, lower_bound, last_iter)
            subset_m2 = self._subset_af_bin(model_2_data, upper_bound, lower_bound, last_iter)
            try:
                auc_m1 = self.calculator.calculate_auc(subset_m1)
                auc_m2 = self.calculator.calculate_auc(subset_m2)
            except ValueError:
                print(
                    f'Could not calculate AUC for allele frequency bin: '
                    f'{lower_bound}-{upper_bound}'
                )
                auc_m1 = np.NaN
                auc_m2 = np.NaN
            if last_iter:
                bin_label = f'{bins_labels[i - 1]} <= x <= {bins_labels[i]}%'
            else:
                bin_label = f'{bins_labels[i - 1]} <= x < {bins_labels[i]}%'
            bin_labels.append(bin_label)

            self._plot_bin(
                ax_afb,
                i,
                bin_label,
                auc_m1,
                subset_m1.shape[0],
                auc_m2,
                subset_m2.shape[0]
            )
        ax_afb.plot(
            np.NaN,
            np.NaN,
            color='red',
            label='= Model 1'
        )
        ax_afb.plot(
            np.NaN,
            np.NaN,
            color='blue',
            label='= Model 2'
        )
        ax_afb.set_xticks(list(range(0, len(bins))), bin_labels, rotation=45)
        ax_afb.set_xlabel('Allele frequency Bin')
        ax_afb.set_ylabel('AUC')
        ax_afb.set_ylim(0.0, 1.0)
        ax_afb.set_xlim(-0.5, len(bins) - 0.5)
        ax_afb.legend(loc=CMPPlottingEnums.LOC.value, bbox_to_anchor=(1.0, 1.01), labelspacing=2)

    @staticmethod
    def _create_auc_label(
            model_1_auc: float,
            model_1_size: int,
            model_2_auc: float,
            model_2_size: int
    ) -> tuple[str, str, str | None]:
        """
        Creates the label for specifically AUC (sub)plots

        Returns tuple of 3:
        - Label for model 1. If element 3 returns None, contains sample size as well.
        - Label for model 2. If element 3 returns None, contains sample size as well.
        - Label for legend title (if sample sizes match).
            Returns None (matplotlib legend title default) if sample
        sizes do not match.
        """
        if model_1_size == model_2_size:
            return f'Model 1: {model_1_auc}', f'Model 2: {model_2_auc}', f'n: {model_1_size}'
        else:
            return f'Model 1: {model_1_auc}\nn: {model_1_size}', \
                   f'Model 2: {model_2_auc}\nn: {model_2_size}', \
                   None

    def _plot_auc(
            self,
            model_1_auc: float,
            model_1_size: int,
            model_2_auc: float,
            model_2_size: int,
            title: str
    ) -> None:
        """
        Plotter function of the Area Under Curve figure.
        Adds the plot to the AUC figure.

        Args:
            model_1_auc:
                The AUC of model 1.
            model_1_size:
                The sample size of model 1.
            model_2_auc:
                The AUC of model 2.
            model_2_size:
                The sample size of model 2.
            title:
                String of what the subplot represents (a consequence or Global).

        """
        # Plotting AUCs
        ax_auc = self.fig_auc.add_subplot(self.n_rows, self.n_cols, self.index)
        labels = self._create_auc_label(
            model_1_auc, model_1_size, model_2_auc, model_2_size
        )

        ax_auc.bar(1, model_1_auc, color='red', label=labels[0])
        ax_auc.bar(2, model_2_auc, color='blue', label=labels[1])

        if math.isnan(model_1_auc):
            ax_auc.text(
                1.5, 0.5, "Not available",
                fontsize='x-large',
                horizontalalignment='center',
                verticalalignment='center'
            )

        ax_auc.set_title(title)
        ax_auc.set_xticks([1, 2], ['Model 1', 'Model 2'])
        ax_auc.set_xlim(0.0, 3.0)
        ax_auc.set_ylim(0.0, 1.0)
        ax_auc.legend(loc=CMPPlottingEnums.LOC.value, bbox_to_anchor=(1.0, 1.02), title=labels[2])

    def _plot_score_dist(
            self,
            model_1_data: pd.DataFrame,
            model_1_size: int,
            model_2_data: pd.DataFrame,
            model_2_size: int,
            title: str
    ) -> None:
        """
        Caller function for creating a boxplot and violinplot of the score distributions.

        Args:
            model_1_data:
                The dataframe of the score and label data of model 1.
            model_1_size:
                The amount of samples in model_1_data.
            model_2_data:
                The dataframe of the score and label data of model 2.
            model_2_size:
                The amount of samples in model_2_data.
            title:
                String of what the subplot represents (a consequence or Global).

        """
        self._create_boxplot_for_column(
            self.fig_score_dist_box,
            ColumnEnums.SCORE.value,
            model_1_data,
            model_1_size,
            model_2_data,
            model_2_size,
            title
        )
        self._create_violinplot_for_column(
            self.fig_score_dist_vio,
            ColumnEnums.SCORE.value,
            model_1_data,
            model_1_size,
            model_2_data,
            model_2_size,
            title
        )

    def _plot_score_diff(
            self,
            model_1_data: pd.DataFrame,
            model_1_size: int,
            model_2_data: pd.DataFrame,
            model_2_size: int,
            title: str
    ) -> None:
        """
        Caller function for creating a boxplot and violinplot of the absolute score differences.

        Args:
            model_1_data:
                The dataframe of the score and label data of model 1.
            model_1_size:
                The amount of samples in model_1_data.
            model_2_data:
                The dataframe of the score and label data of model 2.
            model_2_size:
                The amount of samples in model_2_data.
            title:
                String of what the subplot represents (a consequence or Global).

        """
        self._create_boxplot_for_column(
            self.fig_score_diff_box,
            CompareModelPerformanceEnums.SCORE_DIFF.value,
            model_1_data,
            model_1_size,
            model_2_data,
            model_2_size,
            title
        )
        self._create_violinplot_for_column(
            self.fig_score_diff_vio,
            CompareModelPerformanceEnums.SCORE_DIFF.value,
            model_1_data,
            model_1_size,
            model_2_data,
            model_2_size,
            title
        )

    @staticmethod
    def _create_boxplot_label(
            model_1_data: pd.DataFrame,
            model_1_size: int,
            model_2_data: pd.DataFrame,
            model_2_size: int,
            return_tuple: bool = False
    ) -> str | tuple[str, str]:
        """
        Generic function to create a boxplot label.

        Args:
            model_1_data:
                The dataframe of the score and label data of model 1.
            model_1_size:
                The amount of samples in model_1_data.
            model_2_data:
                The dataframe of the score and label data of model 2.
            model_2_size:
                The amount of samples in model_2_data.
            return_tuple:
                Whenever the result should be returned as tuple (True) or single string (False)
        Returns:
            out:
                Tuple (in case return_tuple=True) containing [0] the label for model 1 and [1]
                the label for model 2. If return_tuple=False,
                returns both labels joined together in a single string.

        """
        n_benign_m1 = model_1_data[model_1_data[ColumnEnums.BINARIZED_LABEL.value] == 0].shape[0]
        n_patho_m1 = model_1_data[model_1_data[ColumnEnums.BINARIZED_LABEL.value] == 1].shape[0]
        n_benign_m2 = model_2_data[model_2_data[ColumnEnums.BINARIZED_LABEL.value] == 0].shape[0]
        n_patho_m2 = model_2_data[model_2_data[ColumnEnums.BINARIZED_LABEL.value] == 1].shape[0]
        return_value = (
            f'Model 1:\nT: {model_1_size}\nB: {n_benign_m1}\nP: {n_patho_m1}',
            f'Model 2:\nT: {model_2_size}\nB: {n_benign_m2}\nP: {n_patho_m2}'
        )
        if return_tuple:
            return return_value
        else:
            return '\n\n'.join(return_value)

    def _create_boxplot_for_column(
            self,
            plot_figure: plt.Figure,
            column_to_plot: str,
            model_1_data: pd.DataFrame,
            model_1_size: int,
            model_2_data: pd.DataFrame,
            model_2_size: int,
            title: str
    ) -> None:
        """
        Plotter function to create a boxplot.
        Adds the plot to the boxplot "plot_figure".

        Args:
            plot_figure:
                The matplotlib.pyplot.Figure object to which the plot add to.
            column_to_plot:
                The column that should be used for plotting boxplot comparison on.
            model_1_data:
                The dataframe of the score and label data of model 1.
            model_1_size:
                The amount of samples in the data of model 1.
            model_2_data:
                The dataframe of the score and label data of model 2.
            model_2_size:
                The amount of samples in the data of model 2.
            title:
                The string of what the subplot should have as title (consequence or Global)

        """
        ax = plot_figure.add_subplot(self.n_rows, self.n_cols, self.index)
        ax.boxplot(
            [
                model_1_data[model_1_data[ColumnEnums.BINARIZED_LABEL.value] == 0][column_to_plot],
                model_2_data[model_2_data[ColumnEnums.BINARIZED_LABEL.value] == 0][column_to_plot],
                model_1_data[model_1_data[ColumnEnums.BINARIZED_LABEL.value] == 1][column_to_plot],
                model_2_data[model_2_data[ColumnEnums.BINARIZED_LABEL.value] == 1][column_to_plot],
            ],
            labels=[
                'Model 1\nBenign',
                'Model 2\nBenign',
                'Model 1\nPathogenic',
                'Model 2\nPathogenic'
            ]
        )
        ax.plot(
            np.NaN,
            np.NaN,
            color='none',
            label=self._create_boxplot_label(
                model_1_data,
                model_1_size,
                model_2_data,
                model_2_size)
        )
        ax.set_ylim(0.0, 1.0)
        ax.set_title(title)
        ax.legend(
            loc=CMPPlottingEnums.LOC.value,
            bbox_to_anchor=(1.0, 1.02),
            handlelength=0
        )

    def _create_violinplot_for_column(
            self,
            plot_figure: plt.Figure,
            column_to_plot: str,
            model_1_data: pd.DataFrame,
            model_1_size: int,
            model_2_data: pd.DataFrame,
            model_2_size: int,
            title: str
    ) -> None:
        """
        Plotter function to create a violin plot.
        Adds the plot to the violin plot "plot_figure".

        Args:
            plot_figure:
                The matplotlib.pyplot.Figure object to which the plot add to.
            column_to_plot:
                The column that should be used for plotting boxplot comparison on.
            model_1_data:
                The dataframe of the score and label data of model 1.
            model_1_size:
                The amount of samples in the data of model 1.
            model_2_data:
                The dataframe of the score and label data of model 2.
            model_2_size:
                The amount of samples in the data of model 2.
            title:
                The string of what the subplot should have as title (consequence or Global)

        """
        ax = plot_figure.add_subplot(self.n_rows, self.n_cols, self.index)
        split = self._assign_violinplot_split(model_1_size, model_2_size)
        sns.violinplot(
            data=pd.concat([model_1_data, model_2_data]),
            x=ColumnEnums.BINARIZED_LABEL.value,
            y=column_to_plot,
            hue=ColumnEnums.DATASET_SOURCE.value,
            ax=ax,
            split=split,
            bw=0.1,
            palette={
                CompareModelPerformanceEnums.MODEL_1.value: 'red',
                CompareModelPerformanceEnums.MODEL_2.value: 'blue'
            },
            legend=False
        )
        labels = self._create_boxplot_label(
            model_1_data, model_1_size, model_2_data, model_2_size, return_tuple=True
        )
        red_patch = mpatches.Patch(color='red', label=labels[0])
        blue_patch = mpatches.Patch(color='blue', label=labels[1])
        ax.set_ylim(0.0, 1.0)
        ax.set_xlim(-0.5, 1.5)
        ax.set_xticks([0.0, 1.0])
        ax.set_xticklabels(['benign', 'pathogenic'])
        ax.set_xlabel('label')
        ax.set_title(title)
        ax.legend(
            handles=[red_patch, blue_patch],
            loc=CMPPlottingEnums.LOC.value,
            bbox_to_anchor=(1.0, 1.02),
            labelspacing=2
        )

    @staticmethod
    def _assign_violinplot_split(
            model_1_size: int,
            model_2_size: int
    ) -> bool:
        """
        Method to check if both model_1_data is present and model_2_data is present.
        Returns True if both model_1_size and model_2_size are not 0. If any of the 2 is 0,
        returns False. This is to prevent ValueError
        "ValueError: There must be exactly two hue levels to use `split`." raise from
        Seaborn.Violinplot.

        Args:
            model_1_size:
                The number of samples from the model 1 dataframe.
            model_2_size:
                The number of samples from the model 2 dataframe.

        Returns:
            bool
                False if either model_1_size is 0 or model_2_size is 0, else True.
        """
        if model_1_size == 0 or model_2_size == 0:
            return False
        else:
            return True
