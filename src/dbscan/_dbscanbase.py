class _DBSCANBase:

    CLUSTER_LABEL_UNCLASSIFIED = -2
    CLUSTER_LABEL_NOISE = -1
    CLUSTER_LABEL_FIRST_CLUSTER = 0

    TECHNICAL_CLUSTER_LABELS = {
        CLUSTER_LABEL_UNCLASSIFIED,
        CLUSTER_LABEL_NOISE
    }

    def __init__(self, eps, min_pts):
        self.eps = eps
        self.min_pts = min_pts
        self.labels = None
        self._next_cluster_label = self.CLUSTER_LABEL_FIRST_CLUSTER
