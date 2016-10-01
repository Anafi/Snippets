
# super graph object
# properties:
# prGRpah primal graph
# fGraph features
# dlGraph (incl. topology) dual graph
# specification: column with id_attribute

import prGraph
import fGraph
import transformFunctions as trF


class SuperGraph:

    def __init__(self, primal_graph, id_column):

        self.id_column = id_column
        self.prGraph = prGraph.prGraph(primal_graph, self.id_column)
        # generate features from wkt, set geometry, attributes
        self.features = self.prGraph.make_features()
        self.fields = fGraph.fGraph(self.features).get_fields()
        self.topology = {point: edge for point, edge in self.prGraph.topology_iter(False)}
        self.dlGraph = trF.graph_to_dual(self.prGraph, break_at_intersections=False)
