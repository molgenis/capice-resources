import json
import math
import numpy as np
import pandas as pd

import xgboost as xgb


class LeafObtainer:

    def __init__(self, model: xgb.XGBClassifier):
        """
        Class to accurately obtain the leaf scores of a given xgboost.XGBClassifier class.

        Parameters
        ----------
        model : xgboost.XGBClassifier
            Un-pickled instance of the to be investigated xgboost XGBClassifier model.
        """
        self.obtain_node = [0]
        self.leaves = []
        self.trees = model.get_booster().get_dump(
            with_stats=True,
            dump_format='json'
        )[0:model.best_iteration+1]

    def reset(self):
        """
        Resets the node to be obtained and the leaves. Use full for an while loop (or apply)
        over a given dataset.
        """
        self.obtain_node = [0]
        self.leaves = []

    def get_leaf_scores(self, data: pd.Series, reset=True, calculate_score=False):
        """
        Method to obtain the leaf scores given a Pandas series.

        Parameters
        ----------
        data : pandas.Series
            The series over which the leaves of the xgboost.XGBClassifier have to be obtained.
        reset : bool
            Whenever to reset the obtain_node and leaves after all leaves have been obtained for
            data.
        calculate_score : bool
            Whenever to instantly return the calculated score of 1/(1+np.exp(-1*sum_of_leaves)).
        Returns
        -------
        leaves : numpy.ndarray
            A single dimension numpy array containing all leaf scores for data.
            Please note: if calculate_score is set to True, leaves will be returned a single value.
        """
        for tree in self.trees:
            tree = json.loads(tree)
            self._obtain_leaf_scores(tree, data)
            self.obtain_node = [0]
        result = np.array(self.leaves)
        if reset:
            self.reset()
        if calculate_score:
            result = 1/(1 + np.exp(-1*result.sum()))
        return result

    def _obtain_leaf_scores(self, tree: dict, data: pd.Series):
        if tree['nodeid'] == self.obtain_node[-1]:
            if 'children' in tree.keys():
                required_feature = tree['split']
                required_value = tree['split_condition']
                data_value = data[required_feature]
                if data_value < required_value or math.isnan(data_value):
                    self.obtain_node.append(tree['yes'])
                else:
                    self.obtain_node.append(tree['no'])
                for child in tree['children']:
                    self._obtain_leaf_scores(child, data)
            else:
                self.leaves.append(tree['leaf'])
