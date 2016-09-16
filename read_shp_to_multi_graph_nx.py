import networkx as nx
from os.path import expanduser

# source: http://stackoverflow.com/questions/30770776/networkx-how-to-create-multidigraph-from-shapefile


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

    ids_excl_attr = [[i.geometry().asPolyline()[0], i.geometry().asPolyline()[-1], i.attributes()] for i in
                     excl_features]
    column_names = [i.name() for i in shp.dataProvider().fields()]

    for i in ids_excl_attr:
        graph.add_edge(i[0], i[1], attr_dict=dict(zip(column_names, i[2])))

    return graph, ids_excl


# source: ess utility functions
def getLayerByName(name):
    layer = None
    for i in QgsMapLayerRegistry.instance().mapLayers().values():
        if i.name() == name:
            layer = i
    return layer


# source: ess utility functions
def getLayerPath4ogr(layer):
    path = ''
    provider = layer.dataProvider()
    provider_type = provider.name()
    # TODO: if provider_type == 'spatialite'
    if  provider_type == 'postgres':
        uri = QgsDataSourceURI(provider.dataSourceUri())
        databaseName = uri.database().encode('utf-8')
        databaseServer = uri.host().encode('utf-8')
        databaseUser = uri.username().encode('utf-8')
        databasePW = uri.password().encode('utf-8')
        path = "PG: host=%s dbname=%s user=%s password=%s" % (
        databaseServer, databaseName, databaseUser, databasePW)
    elif provider_type == 'ogr':
        uri = provider.dataSourceUri()
        path = uri.split("|")[0]
    elif provider_type == 'memory':
        # save temp file in home directory
        home = expanduser("~")
        path = home + '/' + layer.name() + '.shp'
        copied_layer = copy_shp(layer,path)
    return path, provider_type


def getAllFeatures(layer):
    allfeatures = {}
    if layer:
        features = layer.getFeatures()
        allfeatures = {feature.id(): feature for feature in features}
    return allfeatures


# copy a temporary layer
def copy_shp(temp_layer,path):
    features_to_copy = getAllFeatures(temp_layer)
    provider = temp_layer.dataProvider()
    writer = QgsVectorFileWriter(path, provider.encoding(), provider.fields(), provider.geometryType(), provider.crs(),
                                 "ESRI Shapefile")

    # TODO: push message
    if writer.hasError() != QgsVectorFileWriter.NoError:
        print "Error when creating shapefile: ", writer.errorMessage()

    for fet in features_to_copy:
        writer.addFeature(fet)

    del writer
    layer = QgsVectorLayer(path, temp_layer.name(),"ogr")
    return layer

# delete saved copy of temporary layer
def del_shp(temp_layer,path):
    # deleteShapeFile
    pass


def read_shp_to_multi_graph(layer_name, simplify=True, geom_attrs=True):

    # 1. open shapefiles from directory/filename
    try:
        from osgeo import ogr
    except ImportError:
        raise ImportError("read_shp requires OGR: http://www.gdal.org/")

    # find if the table with the give table_name is a shapefile or a postgis file
    layer = getLayerByName(layer_name)
    path, provider_type = getLayerPath4ogr(layer)

    # TODO: convert path string to raw string
    # TODO: push error message when path is empty/does not exist/connection with db does not exist
    if path == '':  # or not os.path.exists(path)
        return

    # construct a multi-graph
    net = nx.MultiGraph()
    lyr = ogr.Open(path)
    count_not_incl = 0
    # 3. open postgis layers
    if provider_type == 'postgres':
        layer = [table for table in lyr if table.GetName() == layer_name][0]
        fields = [x.GetName() for x in layer.schema]
    elif provider_type in ('ogr','memory'):
        layer = lyr[0]
        fields = [x.GetName() for x in layer.schema]
    for f in layer:
        flddata = [f.GetField(f.GetFieldIndex(x)) for x in fields]
        g = f.geometry()
        attributes = dict(zip(fields, flddata))
        attributes["ShpName"] = lyr.GetName()
        # Note:  Using layer level geometry type
        if g.GetGeometryType() == ogr.wkbLineString:
            for edge in edges_from_line(g, attributes, simplify, geom_attrs):
                e1, e2, attr = edge
                net.add_edge(e1, e2, attr_dict=attr)
        elif g.GetGeometryType() == ogr.wkbMultiLineString:
            for i in range(g.GetGeometryCount()):
                geom_i = g.GetGeometryRef(i)
                for edge in edges_from_line(geom_i, attributes, simplify, geom_attrs):
                    e1, e2, attr = edge
                    net.add_edge(e1, e2, attr_dict=attr)
        else:
            count_not_incl += 1
            #TODO: push message x features not included

    if provider_type == 'postgres':
        # destroy connection with db
        lyr.Destroy()
    elif provider_type == 'memory':
        # delete shapefile
        pass

    return net


def edges_from_line(geom, attrs, simplify=True, geom_attrs=True):
    """
    Generate edges for each line in geom
    Written as a helper for read_shp
    Parameters
    ----------
    geom:  ogr line geometry
        To be converted into an edge or edges
    attrs:  dict
        Attributes to be associated with all geoms
    simplify:  bool
        If True, simplify the line as in read_shp
    geom_attrs:  bool
        If True, add geom attributes to edge as in read_shp
    Returns
    -------
     edges:  generator of edges
        each edge is a tuple of form
        (node1_coord, node2_coord, attribute_dict)
        suitable for expanding into a networkx Graph add_edge call
    """
    try:
        from osgeo import ogr
    except ImportError:
        raise ImportError("edges_from_line requires OGR: http://www.gdal.org/")

    if geom.GetGeometryType() == ogr.wkbLineString:
        if simplify:
            edge_attrs = attrs.copy()
            last = geom.GetPointCount() - 1
            if geom_attrs:
                edge_attrs["Wkb"] = geom.ExportToWkb()
                edge_attrs["Wkt"] = geom.ExportToWkt()
                edge_attrs["Json"] = geom.ExportToJson()
            yield (geom.GetPoint_2D(0), geom.GetPoint_2D(last), edge_attrs)
        else:
            for i in range(0, geom.GetPointCount() - 1):
                pt1 = geom.GetPoint_2D(i)
                pt2 = geom.GetPoint_2D(i + 1)
                edge_attrs = attrs.copy()
                if geom_attrs:
                    segment = ogr.Geometry(ogr.wkbLineString)
                    segment.AddPoint_2D(pt1[0], pt1[1])
                    segment.AddPoint_2D(pt2[0], pt2[1])
                    edge_attrs["Wkb"] = segment.ExportToWkb()
                    edge_attrs["Wkt"] = segment.ExportToWkt()
                    edge_attrs["Json"] = segment.ExportToJson()
                    del segment
                yield (pt1, pt2, edge_attrs)

