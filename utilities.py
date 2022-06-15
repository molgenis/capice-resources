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
        paths : pandas.DataFrame
            An X by Y dimensional DataFrame containing the tree number, the features, the data
            values for the features, the model values for said features and if the path goes to
            the YES side or NO side of a node. Final column is always "leaf".

            X dimension depends on the amount of features within the model and the complexity of
            the model. More features = more complexity = more dimensions.
            Y dimension depends on the best training iteration of the XGBoost model. The faster
            the model reaches it's peak performance, the less Y dimensions you will end up with.
        """
        self.obtain_node = [0]
        self.current_path = []
        self.path_collection = []
        self.leaves = []
        print('Starting extracting trees from model.')
        for tree in self.trees:
            tree = json.loads(tree)
            self._obtain_node_information(tree, data)
            self.path_collection.append('=>'.join(self.current_path))
            self.current_path = []
            self.obtain_node = [0]
        print('Finished extracting trees from model.')

        print('Starting conversion from paths to dataframe.')
        result = self._convert_paths_list_to_dataframe(self.path_collection)
        print('Finished conversion from paths to dataframe.')

        print('Starting removal of duplicated entries within dataframe.')
        before_drop = result.shape[0]
        result = self._process_duplicates(result)
        after_drop = result.shape[0]
        print(f'Done. Dropped {before_drop - after_drop} entries.')
        return result

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

        self._save_path_information(required_feature, required_value, data_value, yesno)

        for child in tree['children']:
            self._obtain_node_information(child, data)

    def _save_path_information(self, feature, value, data_value, yesno):
        self.current_path.append(f'{feature}({data_value}<{value}->{yesno})')

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

    def get_paths(self):
        """
        Method to only obtain the paths for a given sample in process_sample().

        Raises
        ------
        ValueError
            If get_leaf_scores() is accessed before process_sample() is performed.

        Returns
        -------
        list
            A list of all the full paths for given sample in process_sample().
        """
        if len(self.path_collection) == 0:
            raise ValueError('process_sample() has to be performed first!')
        return self.path_collection

    @staticmethod
    def _convert_paths_list_to_dataframe(paths: list):
        longest_path = 0
        arrays = []
        index = 1

        for path in paths:
            splitted_path = path.split('=>')
            length_path = len(splitted_path)
            if length_path > longest_path:
                longest_path = length_path
            features = []
            entry_values = []
            model_values = []
            yes_nos = []
            leaf = 0
            for node in splitted_path:
                if node.startswith('leaf'):
                    leaf = float(node.split('leaf(')[1].split(')')[0])
                else:
                    features.append(node.split('(')[0])
                    entry_values.append(node.split('(')[1].split('<')[0])
                    model_values.append(node.split('<')[1].split('->')[0])
                    yes_nos.append(node.split('->')[1].split(')')[0])
            features_dict = {'tree_number': index}
            for i in range(1, length_path):
                features_dict[f'feature_{i}'] = features[i - 1]
                features_dict[f'data_value_{i}'] = entry_values[i - 1]
                features_dict[f'model_value_{i}'] = model_values[i - 1]
                features_dict[f'yes_no_{i}'] = yes_nos[i - 1]
            features_dict['leaf'] = leaf
            arrays.append(pd.Series(features_dict).T)
            index += 1
        reindex = ['tree_number']
        for i in range(1, longest_path):
            reindex.append(f'feature_{i}')
            reindex.append(f'data_value_{i}')
            reindex.append(f'model_value_{i}')
            reindex.append(f'yes_no_{i}')
        reindex.append('leaf')
        result = pd.concat(arrays, axis=1).reindex(reindex).T
        return result

    @staticmethod
    def _process_duplicates(data: pd.DataFrame):
        data_copy = data.copy(deep=True)
        cols = data_copy.columns.difference(['leaf', 'tree_number'], sort=False)
        data_copy['uids'] = data_copy[cols].astype(str).agg('_'.join, axis=1)
        uuids = data_copy['uids'].unique()
        actually_processed_uids = []
        for uid in uuids:
            node_data = data_copy[data_copy['uids'] == uid]
            if node_data.shape[0] >= 2:
                actually_processed_uids.append(uid)
                first_hit = node_data.index[0]
                indexes_to_remove = list(node_data.index[1:])
                sum_of_leaves = node_data['leaf'].sum()
                data_copy.loc[first_hit, 'leaf'] = sum_of_leaves
                data_copy.drop(index=indexes_to_remove, inplace=True)
        data_copy.drop(columns=['uids'], inplace=True)
        return data_copy


def calculate_capice_score(leaves: np.array):
    """
    Convert a numpy array of all leaf scores through the 1/(1+numpy.exp(leaves.sum())) formula.

    Parameters
    ----------
    leaves : numpy.array
        The leaf scores in numpy array format.

    Returns
    -------
    float
        The supposed 1 - CAPICE score for all leaves for a single sample.
    """
    return 1 - (1/(1+np.exp(leaves.sum())))
