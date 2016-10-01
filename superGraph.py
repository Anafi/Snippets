
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

    def __init__(self, primal_graph, id_column):
        self.prGraph = primal_graph

        self.id_column = id_column
        # generate features from wkt, set geometry, attributes

        features = []
        for edge in self.prGraph.edges(data=True):
            feat = QgsFeature()
            feat.setGeometry(QgsGeometry.fromWkt(edge[2]['Wkt']))
            feat.setAttributes(edge[2].values())
            features.append(feat)
        self.features = features

        self.fields = self.features[0].fields()
        self.topology = {point: edge for point, edge in topology_iter(self.prGraph, id_column, False)}
        self.dlGraph = graph_to_dual(self.prGraph, id_column, break_at_intersections=False)

    # make feat_id: wkt_geom dictionary
    def make_wkt_dict(self):
        return { edge[2][self.id_column]:edge[2]['Wkt'] for edge in self.prGraph.edges(data=True)}

    # make feat_id: attributes dictionary
    def make_attr_dict(self):
        return { edge[2][self.id_column]:edge[2] for edge in self.prGraph.edges(data=True)}

    # make feature list
    def feat_generator(self):
        for i in self.features:
            yield i

    # create features
    def create_features(self):
        for i in self.features


    # methods on features

    def rmv_features(self, features_ids, uid):
        new_features = [feat for feat in self.features if feat[uid] not in features_ids]
        # rmv prGraph edges
        #rmv_pr_edges_coords = [(),() for feat in self.prGraph.eddes(data=True) if uid in ...]
        #self.prGraph.remove_edges_from(rmv_pr_edges_coords)
        #rmv_dl_edges_sets =
        #self.dlGraph.remove_edges_from(rmv_dl_edges_sets)
        # rmv dlGraph edges

        return SuperGraph(self.prGraph, self.id_column)

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

    def make_shp(self, crs):
        network = QgsVectorLayer ('LineString?crs=' + crs.toWkt(), "network", "memory")
        QgsMapLayerRegistry.instance().addMapLayer(network)
        pr = network.dataProvider()
        network.startEditing()
        pr.addAttributes([QgsField(i.name(), i.type()) for i in self.fields])
        pr.addFeatures(self.features)
        network.commitChanges()

    def make_dl_shp(self,crs):
        dual_to_shp(crs, self.features, self.dlGraph,Features(self.features).fid_to_uid(self.id_column))

    def find_breakages(self, id_column):
        uid = Features(self.features).fid_to_uid(id_column)
        geometries = Features(self.features).make_geom_dict('feature_id')
        for feat, inter_lines in inter_lines_iter(self.features):
            f_geom = geometries[feat]
            breakages = []
            for line in inter_lines:
                intersection = f_geom.intersection(geometries[line])
                if intersection.wkbType() == 1 and point_is_vertex(intersection, f_geom):
                    breakages.append(intersection)
                # TODO: test multipoints
                elif intersection.wkbType() == 4:
                    for point in intersection.asGeometryCollection():
                        if point_is_vertex(intersection, f_geom):
                            breakages.append(point)
            if len(breakages) > 0:
                yield uid[feat], set([vertex for vertex in find_vertex_index(breakages, feat, geometries)])


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

    # dictionary of feature_id: feature_attribute key, values

    def make_attr_dict(self,id_column):
        if id_column == 'feature_id':
            return {i.id():i.attributes() for i in self.features}
        else:
            return {i[id_column]:i.attributes() for i in self.features}

    # dictionary of feature_id: feature key, values

    def make_feat_dict(self,id_column):
        if id_column == 'feature_id':
            return {i.id():i for i in self.features}
        else:
            return {i[id_column]:i for i in self.features}

    # dictionary of feature_id: attr_column key,values

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






# analyse a super graph


class SuperGraphAnalysis:

    def __init__(self, analysis_type, super_graph, id_column):
        self.analysis_type = analysis_type
        self.uid = id_column
        self.sGrpah = super_graph



    def clean_duplicates(self, sGraph, id_column):
        # remove nodes
        uid = Features(sGraph.features).fid_to_uid(id_column)
        for point, edge in topology_iter(sGraph.prGraph, id_column, False):
            lengths = []
            return sGraph

    def merge(self,sGraph,uid,criterion):
        if criterion == 'conectivity 2':
            pass
        elif criterion == 'azimuth':
            pass


# break multiparts is not needed as the construction of the primal_graph removes multipolylines
# multi-part geometries iterator
# get invalids is not needed


def multi_part_iter(geometries):
    multiparts = {i: j for i, j in geometries.items() if j.wkbType() == 5}
    for k, v in multiparts.items():
        yield (k, v.asGeometryCollection())


# iterator that returns a feature and a list of lines that intersects with, using spatial index
# limitation: no multiparts are allowed


def inter_lines_iter(features):
    spIndex = QgsSpatialIndex()  # create spatial index object
    # insert features to index
    for f in features:
        spIndex.insertFeature(f)
    # find lines intersecting other lines
    for i in features:
        inter_lines = spIndex.intersects(QgsRectangle(QgsPoint(i.geometry().asPolyline()[0]), QgsPoint(i.geometry().asPolyline()[-1])))
        yield i.id(), inter_lines


def find_vertex_index(points,feat,geometries):
    for point in points:
        yield geometries[feat].asPolyline().index(point.asPoint())


def point_is_vertex(point,line):
    if point.asPoint() in line.asPolyline()[1:-1]:
        return True


from itertools import tee, izip

# source: https://docs.python.org/2/library/itertools.html


def pairwise(iterable):
    a, b = tee(iterable)
    next(b, None)
    return izip(a, b)


def break_features(sGraph):
    new_broken_feat = []
    feat_to_del_ids = []
    id_column = sGraph.id_column
    geometries = Features(sGraph.features).make_geom_dict('feature_id')
    attributes = Features(sGraph.features).make_attr_dict(id_column)
    uid = Features(sGraph.features).fid_to_uid(id_column)
    uid_rev = {v: k for k, v in uid.items()}
    for line_to_break, indices in sGraph.find_breakages(id_column):
        list(indices).sort()
        attr = attributes[line_to_break]
        count = 1
        feat_to_del_ids.append(line_to_break)
        for endpoints in pairwise(list(indices)):
            points = []
            for i in range(endpoints[0], endpoints[1]+1):
                points.append(QgsGeometry().fromPoint(geometries[uid_rev[line_to_break]].asPolyline()[i]).asPoint())
            new_geom = QgsGeometry().fromPolyline(points)
            new_feat = QgsFeature()
            new_feat.setGeometry(new_geom)
            new_feat.setAttributes(attr + [uid[line_to_break] + 'br_id_' + str(count)])
            count += 1
            new_broken_feat.append(new_feat)
    new_fields = sGraph.fields + [QgsField('broken_id',QVariant.String)]

    return new_broken_feat, feat_to_del_ids, new_fields

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










