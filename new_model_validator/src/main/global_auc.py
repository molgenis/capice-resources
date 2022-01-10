import os

import pandas as pd
from matplotlib import pyplot as plt
from sklearn.metrics import roc_curve, auc


class GlobalAUC:
    def __init__(self, old_model_data_path, new_model_data_path, output):
        self.old = os.path.abspath(old_model_data_path)
        self.new = os.path.abspath(new_model_data_path)
        self.output = output
        self.rounding = 4

    def compare(self, old_model_data: pd.DataFrame, new_model_data: pd.DataFrame):
        fpr_old, tpr_old, _ = roc_curve(
            y_true=old_model_data['binarized_label'],
            y_score=old_model_data['score']
        )
        auc_old = round(auc(fpr_old, tpr_old), self.rounding)

        fpr_new, tpr_new, _ = roc_curve(
            y_true=new_model_data['binarized_label'],
            y_score=new_model_data['score']
        )
        auc_new = round(auc(fpr_new, tpr_new), self.rounding)

        fig, axes = plt.subplots(1, 1, figsize=(20, 8))
        axes.plot(fpr_old, tpr_old, color='red', label=f'Old (AUC={auc_old})')
        axes.plot(fpr_new, tpr_new, color='blue', label=f'New (AUC={auc_new})')
        axes.set_xlim([0.0, 1.05])
        axes.set_ylim([0.0, 1.05])
        axes.set_xlabel('False Positive Rate')
        axes.set_ylabel('True Positive Rate')
        axes.legend(loc='lower right')
        fig.suptitle('Global AUC comparison between old and new models.')
        axes.set_title(f'Old: {self.old}\nNew: {self.new}')
        export_path = os.path.join(self.output, 'global_auc.png')
        plt.savefig(export_path)
