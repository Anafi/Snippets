import itertools
import networkx as nx

def graph_to_dual(snapped_graph, id_column, inter_to_inter=False):
    # construct a dual graph with all connections
    dual_graph_edges = []
    # all lines
    if not inter_to_inter:
        for i, j in snapped_graph.adjacency_iter():
            edges = []
            for k, v in j.items():
                edges.append(v[0][id_column])
            dual_graph_edges += [x for x in itertools.combinations(edges, 2)]
    # only lines with connectivity 2
    if inter_to_inter:
        for i, j in snapped_graph.adjacency_iter():
            edges = []
            if len(j) == 2:
                for k, v in j.items():
                    edges.append(v[0][id_column])
            dual_graph_edges += [x for x in itertools.combinations(edges, 2)]
    dual_graph = nx.MultiGraph()
    dual_graph.add_edges_from(dual_graph_edges)
    # add nodes (some lines are not connected to others because they are pl)
    for e in snapped_graph.edges_iter(data=id_column):
        dual_graph.add_node(e[2])
    return dual_graph
