from qgis.core import *
import processing
import networkx as nx
from PyQt4.QtCore import QVariant

# select not classified and unclassified from os_road

expr_os_road = QgsExpression("class= 'Not Classified' OR class='Unclassified'")

os_road_shp_path = 'C:/Users/I.Kolovou/Desktop/itn/ROAD_sample.shp'
os_road_sel_shp_path = 'C:/Users/I.Kolovou/Desktop/itn/os_road_sel.shp'
os_road = QgsVectorLayer(os_road_shp_path, "os_road_sample", "ogr")

provider = os_road.dataProvider()
os_road_writer = QgsVectorFileWriter(os_road_sel_shp_path, provider.encoding(), provider.fields(), provider.geometryType(),
                                        provider.crs(), "ESRI Shapefile")

if os_road_writer.hasError() != QgsVectorFileWriter.NoError:
    print "Error when creating shapefile: ", os_road_writer.errorMessage()

for feat in os_road.getFeatures(QgsFeatureRequest(expr_os_road)):
    os_road_writer.addFeature(feat)

del os_road_writer

os_road_sel = QgsVectorLayer(os_road_sel_shp_path, "os_road_sel", "ogr")

# select junctions and roadEnd from os_road_nodes

expr_os_node = QgsExpression("formOfNode= 'junction' OR formOfNode='roadEnd' OR formOfNode='roundabout'")

os_node_shp_path = 'C:\Users\I.Kolovou\Desktop\itn\osroadnode_sample.shp'
os_node = QgsVectorLayer(os_node_shp_path, "os_node_sample", "ogr")

os_node_dict = {(int(i.geometry().asPoint()[0]), int(i.geometry().asPoint()[1])): i.attributes() for i in os_node.getFeatures(QgsFeatureRequest(expr_os_node))}

# join meridian motorways, a-roads and b-roads in one shapefile
meridian_motorways_path = 'C:/Users/I.Kolovou/Desktop/itn/motorway_polyline_sample.shp'
meridian_a_roads_path = 'C:/Users/I.Kolovou/Desktop/itn/a_road_polyline_sample.shp'
meridian_b_roads_path = 'C:/Users/I.Kolovou/Desktop/itn/b_road_polyline_sample.shp'
meridian_motorways = QgsVectorLayer(meridian_motorways_path, "meridian_motorways", "ogr")
meridian_a_roads = QgsVectorLayer(meridian_a_roads_path, "meridian_a_roads", "ogr")
meridian_b_roads = QgsVectorLayer(meridian_b_roads_path, "meridian_b_roads", "ogr")
meridian_shp_path = 'C:/Users/I.Kolovou/Desktop/itn/meridian.shp'

# TODO: add class column for motorways, a roads and b roads
processing.runalg("qgis:mergevectorlayers", [meridian_motorways, meridian_a_roads, meridian_b_roads], meridian_shp_path)

meridian = QgsVectorLayer(meridian_shp_path, "meridian_sample", "ogr")

meridian_buffer_shp_path = 'C:/Users/I.Kolovou/Desktop/itn/meridian_buffer.shp'
meridian_buffer = processing.runandload("qgis:fixeddistancebuffer", meridian, 10, 5, False, meridian_buffer_shp_path)

# create a graph from os road layer

def update_feat_id_col(shp, col_name, start):
    pr = shp.dataProvider()
    fieldIdx = shp.dataProvider().fields().indexFromName(col_name)
    if fieldIdx == -1:
        pr.addAttributes([QgsField(col_name, QVariant.Int)])
        fieldIdx = shp.dataProvider().fields().indexFromName(col_name)
    fid = 1
    updateMap = {}
    if start == 0:
        for f in shp.dataProvider().getFeatures():
            updateMap[f.id()] = {fieldIdx: f.id()}
    elif start == 1:
        for f in shp.dataProvider().getFeatures():
            updateMap[f.id()] = {fieldIdx: fid}
            fid+=1
    shp.dataProvider().changeAttributeValues(updateMap)

# parallel lines are not included as this is not disconnections

def read_shp_to_graph(shp_path):
    graph_shp = nx.read_shp(str(shp_path), simplify=True)
    graph = nx.MultiGraph(graph_shp.to_undirected(reciprocal=False))
    return graph

update_feat_id_col(os_road_sel, 'feat_id', 0)
QgsMapLayerRegistry.instance().addMapLayer(os_road_sel)
os_road_graph = read_shp_to_graph(os_road_sel_shp_path)

# TODO: filter connectivity of nodes that are within a buffer from the meridian
# TODO: use identifier (os_node) and startNode - endNode instead (os_road) OR build graph based on identifier
nodes_con_1 = [node for node in os_road_graph.nodes() if len(os_road_graph.neighbors(node)) == 1]

junctions = {}
junction_to_join_coords = []
roadEnds = {}
for i in nodes_con_1:
    attr = os_node_dict.get((int(i[0]), int(i[1])))
    if attr is None:
        pass
    else:
        formOfNode = attr[1]
        if formOfNode == 'junction' or formOfNode == 'roundabout':
            junctions[i] = attr[1]
            junction_to_join_coords.append((int(i[0]), int(i[1])))
        elif formOfNode == 'roadEnd':
            roadEnds[i] = attr[1]


edge_dict = {i.id(): i.geometry().asPolyline() for i in os_road_sel.getFeatures()}
edge_feat_dict = {i.id(): i for i in os_road_sel.getFeatures()}
meridian_geom_dict = {i.id(): i.geometryAndOwnership() for i in meridian.getFeatures()}

provider = meridian.dataProvider()
spIndex = QgsSpatialIndex()  # create spatial index object
feat = QgsFeature()
fit = provider.getFeatures()  # gets all features in layer
# insert features to index
while fit.nextFeature(feat):
    spIndex.insertFeature(feat)
# find lines intersecting other lines
closest_lines = {(int(i[0]),int(i[1])): spIndex.nearestNeighbor(QgsPoint(i[0], i[1]), 1) for i in junction_to_join_coords}

def PointEquality(vertex1,vertex2):
    return ((abs(vertex1[0] - vertex2[0]) < 0.000001) and
            (abs(vertex1[1] - vertex2[1]) < 0.000001))

edges_to_join = {}
for e in os_road_graph.edges(data=True):
    ind = len(edge_dict[e[2]['feat_id']])-1
    # TODO: if there is another vertex closer to the new point use this vertex and delete the remaining vertices
    if e[0] in junctions.keys():
        closest_line = closest_lines[(int(e[0][0]), int(e[0][1]))]
        if (int(edge_dict[e[2]['feat_id']][0][0]), int(edge_dict[e[2]['feat_id']][0][1])) == (int(e[0][0]),int(e[0][1])):
            ind = 0
        # TODO: check which of the closest lines to use
        new_point = meridian_geom_dict[closest_line[0]].nearestPoint(QgsGeometry().fromPoint(QgsPoint(e[0][0], e[0][1])))
        # eliminate those that the closest_point is the vertex of the segment to be joined to the meridian
        if not PointEquality(new_point.asPoint(), e[0]):
            edges_to_join[e[0]] = {'line':e[2]['feat_id'], 'index':ind,'closest_neigh':closest_line, 'closest_point':new_point.asPoint()}
    elif e[1] in junctions.keys():
        closest_line = closest_lines[(int(e[1][0]), int(e[1][1]))]
        if (int(edge_dict[e[2]['feat_id']][0][0]), int(edge_dict[e[2]['feat_id']][0][1])) == (int(e[1][0]), int(e[1][1])):
            ind = 0
        # TODO: check which of the closest lines to use
        new_point = meridian_geom_dict[closest_line[0]].nearestPoint(QgsGeometry().fromPoint(QgsPoint(e[1][0], e[1][1])))
        # eliminate those that the closest_point is the vertex of the segment to be joined to the meridian
        if not PointEquality(new_point.asPoint(), e[1]):
            edges_to_join[e[1]] = {'line':e[2]['feat_id'], 'index': ind, 'closest_neigh': closest_line, 'closest_point': new_point.asPoint()}

feat_to_del = []
new_feat = {}
for vertex, info in edges_to_join.items():
    feat_to_del.append(info['line'])
    old_feat = edge_feat_dict[info['line']]
    # TODO: fix
    if info['line'] in new_feat.keys():
        old_feat = new_feat[info['line']].geometryAndOwnership()
    geom = old_feat.geometry()
    geom.moveVertex(info['closest_point'][0], info['closest_point'][1], info['index'])
    feat = QgsFeature()
    feat.setGeometry(geom)
    feat.setAttributes(old_feat.attributes())
    new_feat[info['line']] = feat


new_feat_list = [j for i,j in new_feat.items()]
os_road_sel.startEditing()
os_road_sel.dataProvider().deleteFeatures(feat_to_del)
os_road_sel.addFeatures(new_feat_list)
os_road_sel.commitChanges()

# TODO: insert vertex on meridian layer where i have the new points
break_points = {}
meridian_feat_dict = {i.id(): i for i in meridian.getFeatures()}
for k, v in edges_to_join.items():
    geom_pl = meridian_geom_dict[v['closest_neigh'][0]].asPolyline()
    for i,j in enumerate(geom_pl):
        if i != 0:
            vertexBef_x = geom_pl[(i - 1) % len(geom_pl)][0]
            vertexAfter_x = geom_pl[i][0]
            # TODO: what if they are negative
            if k[0] <= vertexBef_x and k[0] >= vertexAfter_x:
                indBefVertex = [(i - 1) % len(geom_pl)]
                break
    break_points[v['closest_neigh'][0]] = {'new_vertex':v['closest_point'], 'indBefVertex': indBefVertex }

feat_to_del = [k for k, v in break_points.items()]
new_feat = {}
for k, v in break_points.items():
    # TODO: fix if geom has more than one breakage points
    feat = QgsFeature()
    geom = meridian_feat_dict[k].geometryAndOwnership()
    if not geom.insertVertex(v['new_vertex'][0], v['new_vertex'][1], v['indBefVertex'][0]):
        print k
    feat.setGeometry(geom)
    feat.setAttributes(meridian_feat_dict[k].attributes())
    new_feat[k] = feat

new_feat_list = [j for i, j in new_feat.items()]
meridian.startEditing()
meridian.dataProvider().deleteFeatures(feat_to_del)
meridian.addFeatures(new_feat_list)
meridian.commitChanges()




# TODO: check deadends but only the ones close to the meridian
edges_to_check = []
for e in os_road_graph.edges(data=True):
    if e[0] in roadEnds.keys() or e[1] in roadEnds.keys():
        edges_to_check.append(e[2]['feat_id'])

os_road_sel = iface.mapCanvas().currentLayer()
os_road_sel.select(edges_to_join)






# get index/indices of line to move on meridian network






# TODO: use v.clean to snap endpoints from the meridian and endpoints of the os road layer after joining them together
# processing.runandload("grass:v.clean", input, 2, 1, None, None, None, output, error_output)


