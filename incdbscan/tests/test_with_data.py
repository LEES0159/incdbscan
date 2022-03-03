from pathlib import Path

import numpy as np
import pytest
from sklearn.cluster import DBSCAN

from incdbscan import IncrementalDBSCAN
from testutils import are_lists_isomorphic


@pytest.mark.slow
def test_same_results_as_sklearn_dbscan():
    base_path = Path(__file__).parent
    data_path = base_path / 'data' / '2d-20c-no0.dat'
    data = np.loadtxt(data_path)[:, 0:2]

    EPS = 1
    MIN_PTS = 5

    dbscan = DBSCAN(eps=EPS, min_samples=MIN_PTS)
    labels_dbscan = dbscan.fit_predict(data)

    incdbscan = IncrementalDBSCAN(eps=EPS, min_pts=MIN_PTS)
    labels_incdbscan_1 = incdbscan.insert(data).get_cluster_labels(data)
    assert are_lists_isomorphic(labels_dbscan, labels_incdbscan_1)

    labels_incdbscan_2 = \
        incdbscan.insert(data).delete(data).get_cluster_labels(data)
    assert are_lists_isomorphic(labels_dbscan, labels_incdbscan_2)

    np.random.seed(123)
    noise = np.random.uniform(-14, 14, (1000, 2))
    labels_incdbscan_3 = \
        incdbscan.insert(noise).delete(noise).get_cluster_labels(data)
    assert are_lists_isomorphic(labels_dbscan, labels_incdbscan_3)