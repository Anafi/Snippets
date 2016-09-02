import networkx as nx

# source: http://stackoverflow.com/questions/30770776/networkx-how-to-create-multidigraph-from-shapefile
def read_multi_shp(path):
    """
    copied from read_shp, but allowing MultiDiGraph instead.
    """
    try:
        from osgeo import ogr
    except ImportError:
        raise ImportError("read_shp requires OGR: http://www.gdal.org/")

    net = nx.MultiDiGraph() # <--- here is the main change I made

    def getfieldinfo(lyr, feature, flds):
            f = feature
            return [f.GetField(f.GetFieldIndex(x)) for x in flds]

    def addlyr(lyr, fields):
        for findex in xrange(lyr.GetFeatureCount()):
            f = lyr.GetFeature(findex)
            flddata = getfieldinfo(lyr, f, fields)
            g = f.geometry()
            attributes = dict(zip(fields, flddata))
            attributes["ShpName"] = lyr.GetName()
            if g.GetGeometryType() == 1:  # point
                net.add_node((g.GetPoint_2D(0)), attributes)
            if g.GetGeometryType() == 2:  # linestring
                attributes["Wkb"] = g.ExportToWkb()
                attributes["Wkt"] = g.ExportToWkt()
                attributes["Json"] = g.ExportToJson()
                last = g.GetPointCount() - 1
                net.add_edge(g.GetPoint_2D(0), g.GetPoint_2D(last), attr_dict=attributes) #<--- also changed this line

    if isinstance(path, str):
        shp = ogr.Open(path)
        lyrcount = shp.GetLayerCount()  # multiple layers indicate a directory
        for lyrindex in xrange(lyrcount):
            lyr = shp.GetLayerByIndex(lyrindex)
            flds = [x.GetName() for x in lyr.schema]
            addlyr(lyr, flds)
    return net


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


def read_shp(path, simplify=True, geom_attrs=True):

    # construct a multi-graph
    net = nx.MultiGraph()

    # 1. open shapefiles from directory/filename
    try:
        from osgeo import ogr
    except ImportError:
        raise ImportError("read_shp requires OGR: http://www.gdal.org/")

    # TODO: convert path string to raw string
    if not isinstance(path, str):
        return

    shp = ogr.Open(path)

    # 2. open temporary shapefiles
    # load layer from mapCanvas()

    #if shp.dataProvider().name() == u'memory':
    fields = [x.name() for x in shp.dataProvider().fields()]
    if simplify:
        pass

    # 3. open postgis layers
    databaseServer = "<IP of database server OR Name of database server"
    databaseName = "<Name of database>"
    databaseUser = "<User name>"
    databasePW = "<User password>"
    connString = "PG: host=%s dbname=%s user=%s password=%s" % (databaseServer, databaseName, databaseUser, databasePW)

    conn = ogr.Open(connString)
    layerList = list(set([i.GetName() for i in conn]))
    conn.Destroy()

    # this is if you open a directory of files

    # for lyr in shp:
        #fields = [x.GetName() for x in lyr.schema]
        #for f in lyr:
        #    flddata = [f.GetField(f.GetFieldIndex(x)) for x in fields]
        #    g = f.geometry()
        #    attributes = dict(zip(fields, flddata))
        #    attributes["ShpName"] = lyr.GetName()
        #    # Note:  Using layer level geometry type
        #    if g.GetGeometryType() == ogr.wkbPoint:
        #        net.add_node((g.GetPoint_2D(0)), attributes)
        #    elif g.GetGeometryType() in (ogr.wkbLineString,
        #                                 ogr.wkbMultiLineString):
        #        for edge in edges_from_line(g, attributes, simplify,
        #                                    geom_attrs):
        #            e1, e2, attr = edge
        #            net.add_edge(e1, e2)
        #            net[e1][e2].update(attr)
        #    else:
        #        raise ImportError("GeometryType {} not supported".
        #                          format(g.GetGeometryType()))

    return net


def edges_from_line(geom, attrs, simplify=True, geom_attrs=True):

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

    elif geom.GetGeometryType() == ogr.wkbMultiLineString:
        for i in range(geom.GetGeometryCount()):
            geom_i = geom.GetGeometryRef(i)
            for edge in edges_from_line(geom_i, attrs, simplify, geom_attrs):
                yield edge