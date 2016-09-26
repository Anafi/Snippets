
# depedencies

from PyQt4.QtCore import QVariant

try:
    import networkx as nx
    from networkx import connected_components
    has_networkx = True
except ImportError, e:
    has_networkx = False



# TODO: clean invalid geometries (1)
# TODO: break multiparts (2)
# TODO: break intersecting lines (3)
# TODO: merge lines (4)
# TODO: clean duplicates (5)
# TODO: clean overlaps (6)


# an object that consist of a primal and a dual graph interconnected


class SuperGraph:

    def __init__(self, features, primal_graph, id_column):
        self.prGraph = primal_graph
        self.features = features
        self.uid = id_column
        # generate features from wkt, set geometry, attributes
        if features is None:
            for edge in self.prGraph.edges(data=True):
                feat = QgsFeature()
                feat.setGeometry(QgsGeometry.fromWkt(edge[2]['Wkt']))
                feat.setAttributes(edge[2].values())

        # self.fields =
        self.topology = {point: edge for point, edge in topology_iter(self.prGraph, id_column, False)}

    # methods on features

    def rmv_features(self, features_ids, uid):
        new_features = [feat for feat in self.features if feat[uid] not in features_ids]
        # rmv prGraph edges
        #rmv_pr_edges_coords = [(),() for feat in self.prGraph.eddes(data=True) if uid in ...]
        #self.prGraph.remove_edges_from(rmv_pr_edges_coords)
        #rmv_dl_edges_sets =
        #self.dlGraph.remove_edges_from(rmv_dl_edges_sets)
        # rmv dlGraph edges

        return SuperGraph(new_features, self.prGraph, self.uid)

    def add_features(self, features_list):
        pass

    # methods on prGraph

    def rmv_edges_pr(self, edges_list):
        self.prGraph.remove_edges_from(edges_list)
        # self.dlGraph.remove_edges_from
        return self.prGraph

    def add_edges_pr(self, edges_list, analysis_col):
        self.prGraph.add_edges_from(edges_list)
        return self.prGraph

    # methods on dlGraph

    def add_nodes_dl(self, nodes_list, analysis_col):
        self.dlGraph.add_nodes(nodes_list)
        self.prGraph.add_edges_from(edges_list)
        # add edges dl
        return self.prGraph, self.dlGraph

    def rmv_nodes_dl(self, nodes_list):
        # rmv edges pr
        # rmv edges dl
        pass


    def move_node(self,node,location):
        pass


# sGraph features methods


class Features:

    def __init__(self,features):
        self.features = features

    # features iterator

    def feature_iter(self):
        for i in self.features:
            yield i

    # dictionary of feature_attr/feature_id : geometries key,values

    def make_geom_dict(self,id_column):
        if id_column == 'feature_id':
            return {i.id():i.geometryAndOwnership() for i in self.features}
        else:
            return {i[id_column]:i.geometryAndOwnership() for i in self.features}

    def make_attr_dict(self,id_column):
        if id_column == 'feature_id':
            return {i.id():i.attributes() for i in self.features}
        else:
            return {i[id_column]:i.attributes() for i in self.features}

    # dictionary of feature_id: feature_attribute key, values

    def fid_to_uid(self, uid_column):
        return {i.id(): i[uid_column] for i in self.features}

    # add attributes to features

    def update_uid(self, column_name, prfx):
        fid = 0
        for feat in self.features:
            feat.setAttributes(feat.attributes() + [prfx + '_' + fid])
            fid += 1

    def update_fields(self, column_name):
        pass

    def make_shp(self, features, crs, encoding, path):
        pass


# analyse a super graph


class SuperGraphAnalysis:

    def __init__(self, analysis_type, super_graph, id_column):
        self.analysis_type = analysis_type
        self.uid = id_column
        self.sGrpah = super_graph

    def break_at_intersections(self, sGraph, id_column):
        uid = Features(sGraph.features).fid_to_uid( id_column)
        # remove nodes
        # add nodes
        geometries = Features(sGraph.features).make_geom_dict('feature_id')
        for comb in inter_lines_iter(sGraph.features, geometries, uid):
            if comb[1] not in dual_graph.neighbors(comb[0]):
                yield comb


    # TODO test
    # this function is not needed as the construction of the primal_graph removes multipolylines

    def break_multiparts(self, sGraph, uid):
        # remove dg nodes that are multiparts
        features = Features(sGraph[0])
        dl_nodes_to_rmv = []
        for feat, geomCol in multi_part_iter(Features(sGraph.features).make_geom_dict(uid)):
            feat_to_rmv.append(feat)
            feat_to_add.append(geomCol)
            # add nodes

    def clean_duplicates(self, sGraph, uid):
        # remove nodes
        return sGraph

    def merge(self,sGraph,uid,criterion):
        if criterion == 'conectivity 2':
            pass
        elif criterion == 'azimuth':
            pass



# multi-part geometries iterator


def multi_part_iter(geometries):
    multiparts = {i: j for i, j in geometries.items() if j.wkbType() == 5}
    for k, v in multiparts.items():
        yield (k, v.asGeometryCollection())


# iterator that returns a feature and a list of lines that intersects with, using spatial index
# limitation: no multiparts are allowed


def inter_lines_iter(features, geometries, uid):
    spIndex = QgsSpatialIndex()  # create spatial index object
    # insert features to index
    for f in features:
        spIndex.insertFeature(f)
    # find lines intersecting other lines
    for i in features:
        inter_lines = spIndex.intersects(QgsRectangle(QgsPoint(i.geometry().asPolyline()[0]), QgsPoint(i.geometry().asPolyline()[-1])))
        for line in inter_lines:
            comb = (i.id(), line)
            geom1 = geometries[comb[0]]
            geom2 = geometries[comb[1]]
            intersection = geom1.intersection(geom2)
            if comb[0] < comb[1] and intersection.wkbType() in [1,4]:
                yield (uid[comb[0]], uid[comb[1]])



# update unique id column on a network
# limitation: works only with shapefiles
# TODO: add function for postgres provider


def update_unqid(layer_name, attr_column, prfx):
    network = getLayerByName(layer_name)
    pr = network.dataProvider()
    fieldIdx = pr.fields().indexFromName(attr_column)
    if fieldIdx == -1:
        pr.addAttributes([QgsField(attr_column, QVariant.String)])
        fieldIdx = pr.fields().indexFromName(attr_column)
    fid = 0
    updateMap = {}
    for f in network.dataProvider().getFeatures():
        updateMap[f.id()] = {fieldIdx: prfx + '_' + str(fid)}
        fid += 1
    pr.changeAttributeValues(updateMap)
    return network


# make super graph from network


def make_sGraph(layer_name, id_column, tolerance, simplify):
    network = getLayerByName(layer_name)
    features = [i for i in network.getFeatures()]
    # invalid geometries are not included
    primal_graph = read_shp_to_multi_graph(layer_name, tolerance, simplify)

    return SuperGraph(features,primal_graph,id_column)










