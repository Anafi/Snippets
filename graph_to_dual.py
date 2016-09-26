import itertools
import networkx as nx


# make topology iterator ( point_coord : [lines] )


def topology_iter(prGraph, id_column, break_at_intersections):
    if break_at_intersections:
        for i, j in prGraph.adjacency_iter():
            edges = [v[0][id_column] for k, v in j.items() if len(j) == 2]
            yield i, edges
    else:
        for i, j in prGraph.adjacency_iter():
            edges = [v[0][id_column] for k, v in j.items()]
            yield i, edges


# make iterator of dual graph edges from prGraph edges


def dl_edges_from_pr_graph(prGraph, id_column, break_at_intersections):
    for point,edges in topology_iter(prGraph,id_column,break_at_intersections):
        for x in itertools.combinations(edges, 2):
            yield x



# make iterator of dual graph nodes from prGraph edges


def dl_nodes_from_pr_graph(prGraph, dlGrpah, id_column):
    for e in prGraph.edges_iter(data=id_column):
        if e[2] not in dlGrpah.nodes():
            yield e[2]


# convert primal graph to dual graph


def graph_to_dual(primal_graph, id_column, break_at_intersections=False):
    dual_graph = nx.MultiGraph()
    dual_graph.add_edges_from([edge for point,edge in dl_edges_from_pr_graph(primal_graph, id_column, break_at_intersections)])
    # add nodes (some lines are not connected to others because they are pl)
    dual_graph.add_nodes_from([node for node in dl_nodes_from_pr_graph(primal_graph, dual_graph, id_column)])
    return dual_graph