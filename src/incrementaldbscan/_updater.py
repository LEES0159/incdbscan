import networkx as nx

from src.incrementaldbscan._labels import (
    CLUSTER_LABEL_UNCLASSIFIED,
    CLUSTER_LABEL_NOISE,
    CLUSTER_LABEL_FIRST_CLUSTER,
    _Labels
)
from src.incrementaldbscan._objects import _Object, _Objects


class _Updater():
    def __init__(self, eps, min_pts, cache_size):
        self.eps = eps
        self.min_pts = min_pts
        self.labels = _Labels()
        self.objects = _Objects(cache_size)
        self.next_cluster_label = CLUSTER_LABEL_FIRST_CLUSTER

    def insertion(self, object_to_insert: _Object):
        print('\nInserting', object_to_insert.id)  # TODO
        self.objects.add_object(object_to_insert)
        self.labels.set_label(
            object_to_insert, CLUSTER_LABEL_UNCLASSIFIED)

        neighbors = self.objects.get_neighbors(object_to_insert, self.eps)
        self._update_neighbor_counts_after_insert(object_to_insert, neighbors)

        new_core_neighbors, old_core_neighbors = \
            self._filter_core_objects_split_by_novelty(neighbors)

        if not new_core_neighbors:
            print('\nnot new_core_neighbors')  # TODO
            # If there is no new core object, only the new object has to be
            # put in a cluster.

            if old_core_neighbors:
                print('old_core_neighbors')
                # If there are already core objects near to the new object,
                # the new object is put in the most recent cluster. This is
                # similar to case "Absorption" in the paper but not defined
                # there.

                label_of_new_object = max([
                    self.labels.get_label(obj) for obj in old_core_neighbors
                ])

            else:
                print('not old_core_neighbors')
                # If the new object does not have any core neighbors,
                # it becomes a noise. Called case "Noise" in the paper.

                label_of_new_object = CLUSTER_LABEL_NOISE

            self.labels.set_label(object_to_insert, label_of_new_object)
            return

        print('\nnew_core_neighbors')  # TODO
        neighbors_of_new_core_neighbors = \
            self._get_neighbors_of_objects(new_core_neighbors)

        update_seeds = self._get_update_seeds(neighbors_of_new_core_neighbors)

        connected_components_in_update_seeds = \
            self._get_connected_components(update_seeds)

        for component in connected_components_in_update_seeds:
            effective_cluster_labels = \
                self._get_effective_cluster_labels_of_objects(component)

            if not effective_cluster_labels:
                print('not effective_cluster_labels')  # TODO
                # If in a connected component of update seeds there are only
                # previously unclassified and noise objects, a new cluster is
                # created. Corresponds to case "Creation" in the paper.

                for obj in component:
                    self.labels.set_label(obj, self.next_cluster_label)
                self.next_cluster_label += 1

            else:
                print('real_cluster_labels')  # TODO
                # If in a connected component of updates seeds there are
                # already clustered objects, all objects in the component
                # will be merged into the most recent cluster.
                # Corresponds to cases "Absorption" and "Merge" in the paper.

                max_label = max(effective_cluster_labels)

                for obj in component:
                    self.labels.set_label(obj, max_label)

                for label in effective_cluster_labels:
                    self.labels.change_labels(label, max_label)

        # Finally all neighbors of each new core object inherits a label from
        # its new core neighbor, thereby affecting border and noise objects,
        # and the object being inserted.

        self._set_cluster_label_to_that_of_new_core_neighbor(
            neighbors_of_new_core_neighbors
        )

    def _update_neighbor_counts_after_insert(self, new_object, neighbors):
        for neighbor in neighbors:
            neighbor.neighbor_count += 1
        new_object.neighbor_count = len(neighbors)

    def _filter_core_objects_split_by_novelty(self, objects):
        new_cores = set()
        old_cores = set()

        for obj in objects:
            if obj.neighbor_count == self.min_pts:
                new_cores.add(obj)
            elif obj.neighbor_count > self.min_pts:
                old_cores.add(obj)

        return new_cores, old_cores

    def _get_neighbors_of_objects(self, objects):
        neighbors = dict()

        for obj in objects:
            neighbors[obj] = self.objects.get_neighbors(obj, self.eps)

        return neighbors

    def _get_update_seeds(self, neighbors_dict):
        """
        During insertion, neighbors_dict holds neighbors of new core neighbors.
        During deletion, neighbors_dict hold neighbors of ex core neighbors.
        """
        seeds = set()

        for neighbors in neighbors_dict.values():
            core_neighbors = [obj for obj in neighbors
                              if obj.neighbor_count >= self.min_pts]
            seeds.update(core_neighbors)

        return seeds

    def _get_connected_components(self, objects):
        if len(objects) == 1:
            return [objects]

        G = nx.Graph()

        for obj in objects:
            neighbors = self.objects.get_neighbors(obj, self.eps)

            for neighbor in neighbors:
                if neighbor in objects:
                    G.add_edge(obj, neighbor)

        return nx.connected_components(G)

    def _get_effective_cluster_labels_of_objects(self, objects):
        non_effective_cluster_labels = set([
            CLUSTER_LABEL_UNCLASSIFIED,
            CLUSTER_LABEL_NOISE
        ])
        effective_cluster_labels = set()

        for obj in objects:
            label = self.labels.get_label(obj)
            if label not in non_effective_cluster_labels:
                effective_cluster_labels.add(label)

        return effective_cluster_labels

    def _set_cluster_label_to_that_of_new_core_neighbor(
            self,
            neighbors_of_new_core_neighbors):

        for new_core, neighbors in neighbors_of_new_core_neighbors.items():
            label = self.labels.get_label(new_core)
            for neighbor in neighbors:
                self.labels.set_label(neighbor, label)

    def deletion(self, object_id):
        print('\nDeleting', object_id)
        object_to_delete = self.objects.get_object(object_id)
        self.objects.remove_object(object_id)

        neighbors = self.objects.get_neighbors(object_to_delete, self.eps)
        self._update_neighbor_counts_after_deletion(neighbors)

        ex_cores = self._get_objects_that_lost_core_property(
            neighbors,
            object_to_delete
        )

        neighbors_of_ex_cores = self._get_neighbors_of_objects(ex_cores)

        update_seeds = self._get_update_seeds(neighbors_of_ex_cores)

        if update_seeds:
            print('\nupdate_seeds')  # TODO

            # def n_components():
            #     return len(self._get_connected_components(update_seeds))

            # def n_components_by_expansion():
            #     return len(
            #         self._get_connected_components_by_expansion(update_seeds))

            # if n_components() > 1 and n_components_by_expansion() > 1:
            #     pass
            #     # Splitting logic

            # else:
            #     pass
            #     # TODO test for reduction? probably not needed but wont hurt

        # Updating labels of border objects that were in the neighborhood
        # of objects that lost their core property is always needed. They
        # become either borders of other clusters or noise.

        self._update_labels_of_border_objects_of_ex_cores(
            neighbors_of_ex_cores)
        self.labels.delete_label(object_id)

    def _get_objects_that_lost_core_property(
            self,
            neighbors,
            object_to_delete):

        ex_core_neighbors = [
            obj for obj in neighbors
            if obj.neighbor_count == self.min_pts - 1
        ]

        # The result has to contain the deleted object if it was core
        if object_to_delete.neighbor_count >= self.min_pts:
            ex_core_neighbors.append(object_to_delete)

        return ex_core_neighbors

    def _update_neighbor_counts_after_deletion(self, neighbors):
        for neighbor in neighbors:
            neighbor.neighbor_count -= 1

    def _update_labels_of_border_objects_of_ex_cores(
            self,
            neighbors_of_ex_cores):

        for ex_core, neighbors_of_ex_core in neighbors_of_ex_cores.items():
            label_of_ex_core = self.labels.get_label(ex_core)

            self._set_border_object_labels_to_largest_around_in_parallel(
                objects_to_set=neighbors_of_ex_core,
                excluded_labels=[label_of_ex_core]
            )

    def _set_border_object_labels_to_largest_around_in_parallel(
            self,
            objects_to_set,
            excluded_labels):

        cluster_updates = {}

        for obj in objects_to_set:
            if obj.neighbor_count < self.min_pts:
                labels = self._get_cluster_labels_in_neighborhood(obj)
                labels.difference_update(excluded_labels)
                if not labels:
                    labels.add(CLUSTER_LABEL_NOISE)

                cluster_updates[obj] = max(labels)

        for obj, new_cluster_label in cluster_updates.items():
            self.labels.set_label(obj, new_cluster_label)

    def _get_cluster_labels_in_neighborhood(self, obj):
        labels = set()

        for neighbor in self.objects.get_neighbors(obj, self.eps):
            label_of_neighbor = self.labels.get_label(neighbor)
            labels.add(label_of_neighbor)

        return labels

    def _get_connected_components_by_expansion(self, objects):
        pass
