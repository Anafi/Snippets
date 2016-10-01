
# imports
import networkx as nx
import utilityFunctions as uF
import shpFunctions as sF
import superGraph

# ----- TRANSFORMATION OPERATORS -----


# ----- SHP TO SGRAPH


def make_sGraph(layer_name, id_column, tolerance, simplify):
    network = uF.getLayerByName(layer_name)
    features = [i for i in network.getFeatures()]
    # invalid geometries are not included
    primal_graph = sF.read_shp_to_multi_graph(layer_name, tolerance, simplify)

    return superGraph(primal_graph,id_column)


# ----- prGRAPH TO FEATURES


def graph_to_features(prGraph):
    wkt_dict = prGraph.make_wkt_dict()
    attr_dict = prGraph.make_attr_dict()
    features = []
    for k, v in wkt_dict.items():
        feat = QgsFeature()
        feat.setAttributes(attr_dict[k])
        feat.setGeometry(QgsGeometry.fromWkt(v))
        features.append(feat)
    return features


# ----- prGRAPH TO dlGRAPH


def graph_to_dual(prGraph, break_at_intersections=False):
    dual_graph = nx.MultiGraph()
    id_column = prGraph.id_column
    dual_graph.add_edges_from(
        [edge for edge in prGraph.dl_edges_from_pr_graph(break_at_intersections)])
    # add nodes (some lines are not connected to others because they are pl)
    dual_graph.add_nodes_from(
        [node for node in prGraph.dl_nodes_from_pr_graph(dual_graph, id_column)])
    return dual_graph


# ----- fGRAPH TO SHP

# TODO: limitation only temp, add path


def make_shp(fGraph, crs):
    network = QgsVectorLayer('LineString?crs=' + crs.toWkt(), "network", "memory")
    QgsMapLayerRegistry.instance().addMapLayer(network)
    pr = network.dataProvider()
    network.startEditing()
    pr.addAttributes([QgsField(i.name(), i.type()) for i in fGraph.get_fields()])
    pr.addFeatures(fGraph.features)
    network.commitChanges()


# ----- dlGRAPH TO SHP

def dual_to_shp(crs, fGraph, dlGraph, id_column):

    centroids = fGraph.make_centroids_dict(id_column)

    # new point layer with centroids
    points = QgsVectorLayer('Point?crs=' + crs.toWkt(), "dual_graph_nodes", "memory")
    QgsMapLayerRegistry.instance().addMapLayer(points)
    pr = points.dataProvider()
    points.startEditing()
    pr.addAttributes([QgsField("id", QVariant.Int)])
    points.commitChanges()
    id = int(0)
    features = []

    for i in centroids.values():
        feat = QgsFeature()
        p = QgsPoint(i[0], i[1])
        feat.setGeometry(QgsGeometry().fromPoint(p))
        feat.setAttributes([id, i[0], i[1]])
        features.append(feat)
        id += int(1)
    points.startEditing()
    pr.addFeatures(features)
    points.commitChanges()

    # new line layer with edge-edge connections
    lines = QgsVectorLayer('LineString?crs=' + crs.toWkt(), "dual_graph_edges", "memory")
    QgsMapLayerRegistry.instance().addMapLayer(lines)
    pr = lines.dataProvider()

    lines.startEditing()
    pr.addAttributes([QgsField("id", QVariant.Int), QgsField("cost", QVariant.Int)])
    lines.commitChanges()

    id = -1
    New_feat = []
    for i in dlGraph.edges(data='cost'):
        id += 1
        new_feat = QgsFeature()
        new_geom = QgsGeometry.fromPolyline(
            [QgsPoint(centroids[i[0]][0], centroids[i[0]][1]), QgsPoint(centroids[i[1]][0], centroids[i[1]][1])])
        new_feat.setGeometry(new_geom)
        new_feat.setAttributes([id, i[2]])
        New_feat.append(new_feat)

    lines.startEditing()
    pr.addFeatures(New_feat)
    lines.commitChanges()

