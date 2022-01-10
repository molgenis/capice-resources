import os
import math

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from sklearn.metrics import roc_auc_score


class ConsequenceAUC:
    def __init__(self, old_model_path, new_model_path, output):
        self.old = os.path.abspath(old_model_path)
        self.new = os.path.abspath(new_model_path)
        self.output = output
        self.rounding = 4

    def compare(self, old_model_data: pd.DataFrame, new_model_data: pd.DataFrame):
        consequences = list(old_model_data['Consequence'].unique())
        ncols = 4
        n_consequences = len(consequences)
        if n_consequences <= ncols:
            row_cols = (1, ncols)
        else:
            row_cols = (math.ceil(n_consequences / ncols), ncols)
        index = 1
        plt.figure(figsize=(20, 40))
        for n, consequence in enumerate(consequences):
            if consequence not in list(new_model_data['Consequence'].unique()):
                continue
            subset_old = old_model_data[old_model_data['Consequence'] == consequence]
            try:
                auc_old = roc_auc_score(
                    y_true=subset_old['binarized_label'],
                    y_score=subset_old['score']
                )
            except ValueError:
                auc_old = np.nan
            subset_new = new_model_data[new_model_data['Consequence'] == consequence]
            try:
                auc_new = roc_auc_score(
                    y_true=subset_new['binarized_label'],
                    y_score=subset_new['score']
                )
            except ValueError:
                auc_new = np.nan
            ax = plt.subplot(row_cols[0], row_cols[1], index)
            ax.bar(1, auc_old, label=f'Old AUC: {round(auc_old, self.rounding)}', color='red')
            ax.bar(2, auc_new, label=f'New AUC: {round(auc_new, self.rounding)}', color='blue')
            ax.set_xlim(0.0, 3.0)
            ax.set_ylim(0.0, 1.0)
            title = '\n'.join(consequence.split('&'))
            ax.set_title(f'{title}')
            ax.legend(loc='lower right')
            ax.set_xticks([1, 2], ['Old', 'New'])
            index += 1
        plt.suptitle(
            f'AUC per consequence plots, comparing old with new.\n'
            f'Old: {self.old}\n'
            f'New: {self.new}\n')
        plt.tight_layout(pad=2.0)
        export_path = os.path.join(self.output, 'consequences.png')
        plt.savefig(export_path)
