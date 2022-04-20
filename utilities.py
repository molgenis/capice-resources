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
        # Leaf specific variables.
        # In lists because the recursive get_leaf_scores would throw errors
        # because the variable was assigned before made.
        self.obtain_node = [0]
        self.leaves = []
        # Path specific variables.
        self.paths = []
        self.current_path = []
        self.dict_current_path = {}
        self.dict_paths = []
        self.current_feat = [0]
        # Linking parents
        self.parents = {}  # Child node ID is key, parent node ID is value
        self.node_ids = {}  # Linking a node ID to the "split"
        self.node_paths = {}  # Node ID is key, path is the value
        # Saving trees.
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
        self.current_path = []
        self.parents = {}

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
            self.paths.append("->".join(self.current_path))
            self.current_path = []
            self.current_feat = [0]
            self.dict_paths.append(self.dict_current_path)
            self.dict_current_path = {}
            self.parents = {}
            self.node_ids = {}
        result = np.array(self.leaves)
        if reset:
            self.reset()
        if calculate_score:
            result = 1/(1 + np.exp(-1*result.sum()))
        return result

    def get_paths(self, kind: str = 'list'):
        """
        Getter function to obtain the paths this class has processed.

        Parameters
        ----------
        kind : str (Optional, default='list')
            The kind of path to return. Can be either list or dict.

        Returns
        -------
        paths : list
            A list containing all the paths in string format as following: feature(
            split_value)->feature(split_value)->UP/DOWN
        """
        if kind != 'list' and kind != 'dict':
            raise AttributeError(f'Kind can be either list or dict, not {kind}')
        if kind == list:
            return self.paths
        else:
            return self.dict_paths

    def _obtain_leaf_scores(self, tree: dict, data: pd.Series):
        if tree['nodeid'] == self.obtain_node[-1]:
            self._process_leaf(tree, data)

    def _process_leaf(self, tree: dict, data: pd.Series):
        if 'children' in tree.keys():
            # TODO list:
            # .1: Save node ID and the split string: DONE
            # .2: Save node ID and parent node ID
            # .3: Save node ID and current path
            # ONCE LEAF IS REACHED:
            # .4: Map node ID's back to string
            # .5: Export paths
            self.current_feat.append(self.current_feat[-1] + 1)
            current_node = tree['nodeid']
            required_feature = tree['split']
            # .1
            self.node_ids[current_node] = required_feature
            required_value = tree['split_condition']
            self.dict_current_path[f'feat_{self.current_feat[-1]}'] = required_feature
            self.dict_current_path[f'value_{self.current_feat[-1]}'] = required_value
            data_value = data[required_feature]
            self.current_path.append(required_feature)
            if data_value < required_value or math.isnan(data_value):
                self.obtain_node.append(tree['yes'])
            else:
                self.obtain_node.append(tree['no'])
            for child in tree['children']:
                self._obtain_leaf_scores(child, data)
        else:
            self.dict_current_path['leaf'] = tree['leaf']
            self.leaves.append(tree['leaf'])
            self._add_leaf_path(tree['leaf'])

    def _obtain_parent_child(self, children: list, parent: dict):
        for child in children:
            self._process_node_ids(current_branch=parent, child_branch=child)

    def _process_node_ids(self, current_branch: dict, child_branch: dict):
        child_id = child_branch['nodeid']
        parent_id = current_branch['nodeid']
        self.parents[child_id] = parent_id
        if child_id not in self.node_ids.keys():
            self.node_ids[child_id] = "_Unique_Separator_".join(
                [child_branch['split'], child_branch['split_condition']])

    def _add_leaf_path(self, leaf: (float, int)):
        if leaf > 0:
            self.current_path.append('UP')
        else:
            self.current_path.append('DOWN')
