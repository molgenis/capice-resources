import json
import time
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
        # Tracking variables
        self.obtain_node = [0]
        # Saving paths
        self.current_path = []
        self.path_collection = []
        self.leaves = []
        # Saving trees.
        self.total_trees = model.best_iteration+1
        self.trees = model.get_booster().get_dump(
            with_stats=True,
            dump_format='json'
        )[0:self.total_trees]

    def process_sample(self, data=pd.Series):
        """
        Method to process a given sample to obtain all walked trees within the CAPICE model.

        Returns
        -------
        leaves : numpy.ndarray
            A single dimension numpy array containing all leaf scores for data.
            Please note: if calculate_score is set to True, leaves will be returned a single value.
        """
        self.obtain_node = [0]
        self.current_path = []
        self.path_collection = []
        self.leaves = []
        print('Starting extracting trees from model.')
        for tree in self.trees:
            tree = json.loads(tree)
            self._obtain_node_information(tree, data)
            self.path_collection.append('->'.join(self.current_path))
            self.current_path = []
            self.obtain_node = [0]
        print('Finished extracting trees from model.')
        return self.path_collection

    def _obtain_node_information(self, tree: dict, data):
        if tree['nodeid'] == self.obtain_node[-1]:
            if 'children' in tree.keys():
                self._process_node(tree, data)
            else:
                self._add_leaf(tree)

    def _process_node(self, tree: dict, data):
        required_feature = tree['split']
        required_value = tree['split_condition']
        data_value = data[required_feature]

        if data_value < required_value or math.isnan(data_value):
            self.obtain_node.append(tree['yes'])
            yesno = 'yes'
        else:
            self.obtain_node.append(tree['no'])
            yesno = 'no'

        self._save_path_information(required_feature, required_value, yesno)

        for child in tree['children']:
            self._obtain_node_information(child, data)

    def _save_path_information(self, feature, value, yesno):
        self.current_path.append(f'{feature}({value})({yesno})')

    def _add_leaf(self, tree):
        leaf = tree['leaf']
        self.current_path.append(f'leaf({leaf})')
        self.leaves.append(leaf)

    def get_leaf_scores(self):
        """
        Method to only obtain the leaf scores for a given sample in process_sample().

        Raises
        ------
        ValueError
            If get_leaf_scores() is accessed before process_sample() is performed.

        Returns
        -------
        list
            A list of all the leaf scores for given sample in process_sample().
        """
        if len(self.leaves) == 0:
            raise ValueError('process_sample() has to be performed first!')
        return self.leaves


def process_duplicates(data: pd.DataFrame, timer=5):
    data_copy = data.copy(deep=True)
    cols = data_copy.columns.difference(['leaf', 'parent_node'], sort=False)
    data_copy['uids'] = data_copy[cols].astype(str).agg('_'.join, axis=1)
    uuids = data_copy['uids'].unique()
    timer_bl = time.time()
    current = 0
    total = len(uuids)
    skipped = 0
    actually_processed_uids = []
    for uid in uuids:
        timer_il = time.time()
        if timer_il - timer_bl > timer:
            print(f'Processing: {current}/{total}')
            timer_bl = time.time()
        node_data = data_copy[data_copy['uids'] == uid]
        if node_data.shape[0] < 2:
            skipped += 1
            current += 1
            continue
        else:
            actually_processed_uids.append(uid)
            first_hit = node_data.index[0]
            indexes_to_remove = list(node_data.index[1:])
            sum_of_leaves = node_data['leaf'].sum()
            data_copy.loc[first_hit, 'leaf'] = sum_of_leaves
            data_copy.drop(index=indexes_to_remove, inplace=True)
            current += 1
    print(f'Done! processed {total} entries, skipped {skipped}.')
    # data_copy.drop(columns=['uids'], inplace=True)
    return data_copy, actually_processed_uids


def calculate_capice_score(leaves: np.array):
    return 1/(1+np.exp(leaves.sum()))
