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
        self.leaves = []
        self.current_path = []
        self.parents = {}

    def get_leaf_scores(self, reset=True, calculate_score=False):
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
        first_iter = True
        for tree in self.trees:
            tree = json.loads(tree)
            if first_iter:
                node_id = tree['nodeid']
                node_feature = tree['split']
                self.node_ids[node_id] = node_feature
                self.node_paths[node_id] = [node_feature]
                first_iter = False
            self._obtain_leaf_scores(tree)
            self.paths.append("->".join(self.current_path))
            self.current_path = []
            self.current_feat = [0]
            self.dict_paths.append(self.dict_current_path)
            self.dict_current_path = {}
            break
            # self.parents = {}
            # self.node_ids = {}
            # self.node_paths = {}
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

    def _obtain_leaf_scores(self, tree: dict):
        # .2
        if 'children' in tree.keys():
            self._add_parent_child(parent=tree, children=tree['children'])

        # .3
        # Temporary check
        if 'children' in tree.keys():
            self._add_path_to_node_id(tree)

        self._process_leaf(tree)

    def _process_leaf(self, tree: dict):
        if 'children' in tree.keys():
            # TODO list:
            # .1: Save node ID as key and the split string as value: DONE
            # .2: Save child node ID as key and parent node ID as value: DONE
            # .3: Save node ID as key and current path as value in list: DONE
            # .4: Remove dependency on yes/no path: DONE
            # .5: Add split value to current path described in .3
            # ONCE LEAF IS REACHED:
            # .4: Map node ID's back to string
            # .5: Export paths

            self.current_feat.append(self.current_feat[-1] + 1)
            current_node = tree['nodeid']
            required_feature = tree['split']

            # .1: Save node ID as key and the split string as value
            self.node_ids[current_node] = required_feature

            required_value = tree['split_condition']
            self.dict_current_path[f'feat_{self.current_feat[-1]}'] = required_feature
            self.dict_current_path[f'value_{self.current_feat[-1]}'] = required_value
            self.current_path.append(required_feature)

            for child in tree['children']:
                self._obtain_leaf_scores(child)
        else:
            self.dict_current_path['leaf'] = tree['leaf']
            self.leaves.append(tree['leaf'])
            self._add_leaf_path(tree['leaf'])

    def _add_parent_child(self, parent: dict, children: list):
        for child in children:
            self.parents[child['nodeid']] = parent['nodeid']

    def _add_path_to_node_id(self, current_tree: dict):
        current_node = current_tree['nodeid']
        current_feature = current_tree['split']
        print('DEBUG MODE')
        print(current_node)
        print(current_feature)
        print(self.parents)
        print(self.node_paths)
        if current_node in self.parents.keys():
            parent_path = self.node_paths[self.parents[current_node]]
            self.node_paths[current_node] = '->'.join([parent_path, current_feature])
        else:
            self.node_paths[current_node] = current_feature

    def _add_leaf_path(self, leaf: (float, int)):
        if leaf > 0:
            self.current_path.append('UP')
        else:
            self.current_path.append('DOWN')
