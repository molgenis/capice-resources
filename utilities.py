import json
import time

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
        # Linking parents
        self.parents = {}  # Child node ID is key, parent node ID is value
        self.yes_no_dict = {}  # Node ID is key, child is either "yes" or "no"
        self.node_ids = {}  # Linking a node ID to the "split"
        self.node_paths = {}  # Node ID is key, path is the value
        self.final_node_paths = {}  # Node ID is key, path is the value
        self.node_path_collection = []
        self.max_length = 0
        # Saving trees.
        self.total_trees = model.best_iteration+1
        self.trees = model.get_booster().get_dump(
            with_stats=True,
            dump_format='json'
        )[0:self.total_trees]

    def get_leaf_scores(self, progress_timer: int = 5):
        """
        Method to obtain the leaf scores given a Pandas series.

        Parameter
        ---------
        progress_timer : int
            Interval time in seconds to print progression statements.

        Returns
        -------
        leaves : numpy.ndarray
            A single dimension numpy array containing all leaf scores for data.
            Please note: if calculate_score is set to True, leaves will be returned a single value.
        """
        first_iter = True
        print('Starting extracting trees from model.')
        for tree in self.trees:
            tree = json.loads(tree)
            if first_iter:
                node_id = tree['nodeid']
                node_feature = tree['split']
                self.node_ids[node_id] = node_feature
                self.node_paths[node_id] = [node_feature]
                first_iter = False
            self._obtain_leaf_scores(tree)
            self._remove_paths_no_leaf()
            self._obtain_max_length()
            self._convert_dict_to_list()
            self.parents = {}
            self.yes_no_dict = {}
            self.node_ids = {}
            self.node_paths = {}
            self.final_node_paths = {}
        print('Finished extracting trees from model.')

        print('Starting converting string to arrays.')
        arrays = self._string_to_array(progress_timer)
        print('Finished converting string to arrays.')

        print('Starting converting arrays to dataframe.')
        result = self._arrays_to_dataframe(arrays)
        print('Finished converting arrays to dataframe.')

        return result

    def _remove_paths_no_leaf(self):
        for key, value in self.node_paths.items():
            if value.endswith('leaf'):
                self.final_node_paths[key] = value

    def _obtain_max_length(self):
        for value in self.final_node_paths.values():
            length = len(value.split('->'))
            if length > self.max_length:
                self.max_length = length

    def _convert_dict_to_list(self):
        for value in self.final_node_paths.values():
            self.node_path_collection.append(value)

    def _string_to_array(self, progress_timer):
        arrays = []
        current_path = 0
        total_paths = len(self.node_path_collection)

        time_bl = time.time()

        for entry in self.node_path_collection:
            time_il = time.time()
            if time_il - time_bl > progress_timer:
                print('Progression converting string to array:')
                print(f'Converted {current_path}/{total_paths}')
                time_bl = time_il
            length = len(entry.split('->'))
            if length > self.max_length:
                self.max_length = length
            features = []
            values = []
            leaf = 0
            for f in entry.split('->'):
                value, feature = f.split('|')
                if feature == 'leaf':
                    leaf = value
                    break
                features.append(feature)
                values.append(value)
            feats = {}
            for i in range(1, length):
                feats[f'feature_{i}'] = features[i - 1]
                feats[f'value_{i}'] = values[i - 1]
            feats['leaf'] = leaf
            arrays.append(pd.Series(feats).T)
            current_path += 1
        return arrays

    def _arrays_to_dataframe(self, arrays: list):
        reindex = []
        for i in range(1, self.max_length):
            reindex.append(f'feature_{i}')
            reindex.append(f'value_{i}')
        reindex.append('leaf')
        df = pd.concat(arrays, axis=1).reindex(reindex).T
        before_drop = df.shape[0]
        df.drop_duplicates(inplace=True)
        after_drop = df.shape[0]
        print(f'Dropped {before_drop - after_drop} entries due to being duplicated.')
        return df.reset_index(drop=True)

    def _obtain_leaf_scores(self, tree: dict):
        has_child = False
        if 'children' in tree.keys():
            has_child = True

        if has_child:
            self._add_parent_child(parent=tree, children=tree['children'])
            self._obtain_yes_no_ids(tree=tree)

        self._add_path_to_node_id(tree)
        if has_child:
            self._process_leaf(tree)

    def _process_leaf(self, tree: dict):
        current_node = tree['nodeid']
        required_feature = tree['split']

        self.node_ids[current_node] = required_feature

        for child in tree['children']:
            self._obtain_leaf_scores(child)

    def _obtain_yes_no_ids(self, tree):
        self.yes_no_dict[tree['yes']] = 'yes'
        self.yes_no_dict[tree['no']] = 'no'

    def _add_parent_child(self, parent: dict, children: list):
        for child in children:
            self.parents[child['nodeid']] = parent['nodeid']

    def _add_path_to_node_id(self, current_tree: dict):
        current_node = current_tree['nodeid']
        if 'split' in current_tree.keys():
            current_feature = '|'.join(
                [str(current_tree['split_condition']), current_tree['split']]
            )
        else:
            leaf_value = str(current_tree['leaf']) + \
                         f'({self.yes_no_dict[current_node]})' + \
                         f'({self.parents[current_node]})'
            current_feature = '|'.join([leaf_value, 'leaf'])
        if current_node in self.parents.keys():
            parent_path = self.node_paths[self.parents[current_node]]
            self.node_paths[current_node] = '->'.join([parent_path, current_feature])
        else:
            self.node_paths[current_node] = current_feature


def process_duplicates(data: pd.DataFrame, timer=5):
    data_copy = data.copy(deep=True)
    cols = data_copy.columns.difference(['leaf', 'yes/no', 'parent_node'], sort=False)
    data_copy['uids'] = data_copy[cols].astype(str).agg('_'.join, axis=1)
    uuids = data_copy['uids'].unique()
    timer_bl = time.time()
    current = 0
    total = len(uuids)
    for uid in uuids:
        timer_il = time.time()
        if timer_il - timer_bl > timer:
            print(f'Processing: {current}/{total}')
            timer_bl = time.time()
        node_data = data_copy[data_copy['uids'] == uid]
        if node_data.shape[0] < 2:
            continue
        first_hit = node_data.index[0]
        indexes_to_remove = list(node_data.index[1:])
        sum_of_leaves = node_data['leaf'].sum()
        data_copy.loc[first_hit, 'leaf'] = sum_of_leaves
        data_copy.drop(index=indexes_to_remove, inplace=True)
        current += 1
    return data_copy
