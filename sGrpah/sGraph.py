
# super graph object
# properties:
# prGRpah primal graph
# fGraph features
# dlGraph (incl. topology) dual graph
# specification: column with id_attribute

#import prGraph
#import fGraph
#import transformFunctions as trF


class SuperGraph:

    def __init__(self, primal_graph, id_column):

        self.id_column = id_column
        self.getprGraph = prGraph(primal_graph, self.id_column)
        # generate features from wkt, set geometry, attributes
        self.getfGraph = fGraph(self.getprGraph.features)
        self.getfields = (self.getfGraph).get_fields()
        self.gettopology = {point: edge for point, edge in self.getprGraph.topology_iter(False)}
