import numpy as np

from src.distance import get_neighbors


class DBSCAN:
    """
    Based on "A Density-Based Algorithm for Discovering Clusters in Large
    Spatial Databases with Noise" by Ester et al. 1996.
    """

    cluster_label_unclassified = -2
    cluster_label_noise = -1
    cluster_label_first_cluster = 0

    def __init__(self, eps, min_samples):
        self.eps = eps
        self.min_samples = min_samples
        self.labels = None

    def _init_fit(self, X):
        self.labels = np.repeat([DBSCAN.cluster_label_unclassified], len(X))
        self._next_cluster_label = DBSCAN.cluster_label_first_cluster

    def _is_point_unclassified(self, ix):
        return self.labels[ix] == DBSCAN.cluster_label_unclassified

    def _is_point_noise(self, ix):
        return self.labels[ix] == DBSCAN.cluster_label_noise

    def _assign_label(self, ix, label):
        self.labels[ix] = label

    def _expand_cluster(self, ix, X):
        point = X[ix]
        seeds = set(get_neighbors(point, X, self.eps))

        if len(seeds) < self.min_samples:
            self._assign_label(ix, DBSCAN.cluster_label_noise)
            return

        for seed in seeds:
            self._assign_label(seed, self._next_cluster_label)

        seeds.remove(ix)

        while len(seeds) > 0:
            seed_point = X[seeds.pop()]  # called currentP in paper
            neighbors_of_seed = get_neighbors(seed_point, X, self.eps)

            if len(neighbors_of_seed) >= self.min_samples:
                for neighbor in neighbors_of_seed:
                    if self._is_point_unclassified(neighbor):
                        seeds.add(neighbor)
                        self._assign_label(neighbor, self._next_cluster_label)
                    elif self._is_point_noise(neighbor):
                        self._assign_label(neighbor, self._next_cluster_label)

        self._next_cluster_label += 1

    def fit(self, X):
        self._init_fit(X)

        for ix in range(len(X)):
            if self._is_point_unclassified(ix):
                self._expand_cluster(ix, X)

        return self