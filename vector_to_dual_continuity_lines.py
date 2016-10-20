import networkx as nx
import math
import itertools
from PyQt4.QtCore import QVariant

databaseServer = "192.168.1.9"
databaseName = "ssx_tombolo"
databaseUser = "ik"
databasePW = "password"



def GetPGLayer( lyr_name, databaseServer, databaseName, databaseUser, databasePW):
    connString = r"PG: host=%s dbname=%s user=%s password=%s" %(databaseServer,databaseName,databaseUser,databasePW)
    conn = ogr.Open(connString)
    if conn is None:
        print 'Could not open a database or GDAL is not correctly installed!'
    lyr = conn.GetLayer( lyr_name )
    if lyr is None:
        print >> sys.stderr, '[ ERROR ]: layer name = "%s" could not be found in database "%s"' % ( lyr_name, databaseName )
        sys.exit( 1 )
    featureCount = lyr.GetFeatureCount()
    print "Number of features in %s: %d" % ( lyr_name , featureCount )
    conn.Destroy()


def read_shp(path, simplify=True, geom_attrs=True):
     try:
         from osgeo import ogr
     except ImportError:
         raise ImportError("read_shp requires OGR: http://www.gdal.org/")

     net = nx.DiGraph()
     shp = ogr.Open(path)
     for lyr in shp:
         fields = [x.GetName() for x in lyr.schema]
         for f in lyr:
             flddata = [f.GetField(f.GetFieldIndex(x)) for x in fields]
             g = f.geometry()
             attributes = dict(zip(fields, flddata))
             attributes["ShpName"] = lyr.GetName()
             # Note:  Using layer level geometry type
             if g.GetGeometryType() == ogr.wkbPoint:
                 net.add_node((g.GetPoint_2D(0)), attributes)
             elif g.GetGeometryType() in (ogr.wkbLineString,
                                          ogr.wkbMultiLineString):
                 for edge in edges_from_line(g, attributes, simplify,
                                             geom_attrs):
                     e1, e2, attr = edge
                     net.add_edge(e1, e2)
                     net[e1][e2].update(attr)
             else:
                 raise ImportError("GeometryType {} not supported".
                                   format(g.GetGeometryType()))
     return net


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

def read_shp_to_graph(shp_path):
    graph_shp = nx.read_shp(str(shp_path), simplify=True)
    shp = QgsVectorLayer(shp_path, "network", "ogr")
    graph = nx.MultiGraph(graph_shp.to_undirected(reciprocal=False))
    # parallel edges are excluded of the graph because read_shp does not return a multi-graph, self-loops are included
    all_ids = [i.id() for i in shp.getFeatures()]
    ids_incl = [i[2]['feat_id'] for i in graph.edges(data=True)]
    ids_excl = set(all_ids) - set(ids_incl)
    request = QgsFeatureRequest().setFilterFids(list(ids_excl))
    excl_features = [feat for feat in shp.getFeatures(request)]
    ids_excl_attr = [[i.geometry().asPolyline()[0], i.geometry().asPolyline()[-1], i.attributes()] for i in excl_features]
    column_names = [i.name() for i in shp.dataProvider().fields()]
    for i in ids_excl_attr:
        graph.add_edge(i[0], i[1], attr_dict=dict(zip(column_names,i[2])))
    return graph


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



# find midpoint between two points
def mid(pt1, pt2):
    x = (pt1.x() + pt2.x())/2
    y = (pt1.y() + pt2.y())/2
    return (x,y)

# find midpoint of a polyline geometry , input geometry type
def pl_midpoint(pl_geom):
    vertices = pl_geom.asPolyline()
    length = 0
    mid_length = pl_geom.length() / 2
    for ind, vertex in enumerate(vertices):
        start_vertex = vertices[ind]
        end_vertex = vertices[(ind +1) % len(vertices)]
        length += math.hypot(abs(start_vertex[0]-end_vertex[0]), abs(start_vertex[1]-end_vertex[1]))
        if length > mid_length:
            ind_mid_before = ind
            ind_mid_after = ind+1
            midpoint = mid(vertices[ind_mid_before], vertices[ind_mid_after])
            break
    return midpoint

def dual_to_shp( path,dual_graph,continuity):
    network = QgsVectorLayer(path,"network", 'ogr')
    network_geom = {f.id():f.geometryAndOwnership() for f in network.getFeatures()}
    centroids = {i.id(): pl_midpoint(i.geometry()) for i in network.getFeatures()}

    # new point layer with centroids
    crs = network.crs()
    points = QgsVectorLayer('Point?crs=' + crs.toWkt(), "dual_graph_nodes", "memory")
    QgsMapLayerRegistry.instance().addMapLayer(points)
    pr = points.dataProvider()
    points.startEditing()
    pr.addAttributes([QgsField("id", QVariant.Int)])
    points.commitChanges()

    id = int(-1)
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
    pr.addAttributes([QgsField("id", QVariant.Int),QgsField("edge1", QVariant.Int),QgsField("edge2", QVariant.Int),QgsField("inter_point", QVariant.String),QgsField("vertex1", QVariant.String),QgsField("vertex2", QVariant.String),QgsField("cost", QVariant.Int)])
    lines.commitChanges()

    id = -1
    New_feat = []

    for i in dual_graph.edges():
        id += 1
        new_feat = QgsFeature()
        new_geom = QgsGeometry.fromPolyline([QgsPoint(centroids[i[0]][0],centroids[i[0]][1]),QgsPoint(centroids[i[1]][0],centroids[i[1]][1])])
        new_feat.setGeometry(new_geom)
        inter_point = network_geom[i[0]].intersection(network_geom[i[1]])

        if continuity==True:
            vertex1 = network_geom[i[0]].asPolyline()[-2]
            if inter_point.asPoint() == network_geom[i[0]].asPolyline()[0]:
                vertex1 = network_geom[i[0]].asPolyline()[1]
            vertex2 = network_geom[i[1]].asPolyline()[-2]
            if inter_point.asPoint() == network_geom[i[1]].asPolyline()[0]:
                vertex2 = network_geom[i[1]].asPolyline()[1]

        elif continuity==False:
            vertex1 = network_geom[i[0]].asPolyline()[0]
            if inter_point.asPoint() == network_geom[i[0]].asPolyline()[0]:
                vertex1 = network_geom[i[0]].asPolyline()[-1]
            vertex2 = network_geom[i[1]].asPolyline()[0]
            if inter_point.asPoint() == network_geom[i[1]].asPolyline()[0]:
                vertex2 = network_geom[i[1]].asPolyline()[-1]

        inter_vertex1 = math.hypot(abs(inter_point.asPoint()[0]-vertex1[0]),abs(inter_point.asPoint()[1]-vertex1[1]))
        inter_vertex2 = math.hypot(abs(inter_point.asPoint()[0]-vertex2[0]),abs(inter_point.asPoint()[1]-vertex2[1]))
        vertex1_2 = math.hypot(abs(vertex1[0]-vertex2[0]),abs(vertex1[1]-vertex2[1]))
        A=((inter_vertex1**2) + (inter_vertex2**2) - (vertex1_2**2))
        B=(2*inter_vertex1*inter_vertex2)
        if B!=0:
            cos_angle = A/B
        else:
            cos_angle = NULL
        if cos_angle<-1:
            cos_angle = int(-1)
        if cos_angle>1:
            cos_angle = int(1)
        cost = math.acos(cos_angle)
        new_feat.setAttributes([id,i[0],i[1],str(inter_point.asPoint()),str(vertex1),str(vertex2),int(180 - math.degrees(cost))])
        New_feat.append(new_feat)

    lines.startEditing()
    pr.addFeatures(New_feat)
    lines.commitChanges()
