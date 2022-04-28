import pandas as pd


class LeafObtainer:
    def __init__(self):
        self.final_node_collection = []
        self.max_length = 0

    def process_string_to_array(self):
        arrays = self._string_to_array()
        return self._arrays_to_dataframe(arrays)

    def _string_to_array(self):
        arrays = []

        for entry in self.final_node_collection:
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
                feats[f'feature_{i}'] = features[i-1]
                feats[f'value_{i}'] = values[i-1]
            feats['leaf'] = leaf
            arrays.append(pd.Series(feats).T)
        return arrays

    def _arrays_to_dataframe(self, arrays: list):
        reindex = []
        for i in range(1, self.max_length):
            reindex.append(f'feature_{i}')
            reindex.append(f'value_{i}')
        reindex.append('leaf')
        return pd.concat(arrays, axis=1).reindex(reindex).T
