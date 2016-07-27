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

expr_os_node = QgsExpression("formOfNode= 'junction' OR formOfNode='roadEnd'")

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

processing.runalg("qgis:mergevectorlayers", [meridian_motorways, meridian_a_roads, meridian_b_roads], meridian_shp_path)

meridian = QgsVectorLayer(meridian_shp_path, "meridian_sample", "ogr")

meridian_buffer_shp_path = 'C:/Users/I.Kolovou/Desktop/itn/meridian_buffer.shp'
meridian_buffer = processing.runandload("qgis:fixeddistancebuffer", meridian, 10, 5, False, meridian_buffer_shp_path )

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

'''filter connectivity of nodes that are within a buffer from the meridian'''
nodes_con_1 = [node for node in os_road_graph.nodes() if len(os_road_graph.neighbors(node)) == 1]

junctions = {}
roadEnds = {}
for i in nodes_con_1:
    attr = os_node_dict.get((int(i[0]), int(i[1])))
    if attr is None:
        pass
    else:
        formOfNode= attr[1]
        if formOfNode == 'junction':
            junctions[i] = attr[1]
        elif formOfNode == 'roadEnd':
            roadEnds[i] = attr[1]

edges_to_join = []
edges_to_check = []
for e in os_road_graph.edges(data=True):
    if e[0] in junctions.keys() or e[1] in junctions.keys():
        edges_to_join.append(e[2]['feat_id'])
    elif e[0] in roadEnds.keys() or e[1] in roadEnds.keys():
        edges_to_check.append(e[2]['feat_id'])

os_road_sel = iface.mapCanvas().currentLayer()
os_road_sel.select(edges_to_join)

'''use identifier (os_node) and startNode - endNode instead (os_road) OR build graph based on identifier'''

# find which features from os_road intersect the buffer of meridian
provider = os_road_sel.dataProvider()
spIndex = QgsSpatialIndex()  # create spatial index object
feat = QgsFeature()
fit = provider.getFeatures()  # gets all features in layer
# insert features to index
while fit.nextFeature(feat):
    spIndex.insertFeature(feat)

os_road_meridian = {i.id(): spIndex.intersects(QgsRectangle()) for i in meridian_buffer.getFeatures() if not i.geometry().isMultipart()}

#(nearest point of one geom to another)
# QgsGeometry  nearestPoint (const QgsGeometry &other) const
# QgsGeometry  shortestLine (const QgsGeometry &other) const



