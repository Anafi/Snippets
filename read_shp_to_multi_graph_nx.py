import networkx as nx
from os.path import expanduser
import os
from decimal import *
import re


# sources: http://stackoverflow.com/questions/30770776/networkx-how-to-create-multidigraph-from-shapefile
#          https://github.com/networkx/networkx/blob/master/networkx/readwrite/nx_shp.py

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
    if provider_type == 'postgres':
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
        copied_layer = copy_shp(layer, path)
    return path, provider_type


def getAllFeatures(layer):
    allfeatures = {}
    if layer:
        features = layer.getFeatures()
        allfeatures = {feature.id(): feature for feature in features}
    return allfeatures


# copy a temporary layer
def copy_shp(temp_layer, path):
    features_to_copy = getAllFeatures(temp_layer)
    provider = temp_layer.dataProvider()
    writer = QgsVectorFileWriter(path, provider.encoding(), provider.fields(), provider.geometryType(), provider.crs(),
                                 "ESRI Shapefile")

    # TODO: push message
    if writer.hasError() != QgsVectorFileWriter.NoError:
        print "Error when creating shapefile: ", writer.errorMessage()

    for fet in features_to_copy.values():
        writer.addFeature(fet)

    del writer
    layer = QgsVectorLayer(path, temp_layer.name(), "ogr")
    return layer


# delete saved copy of temporary layer
def del_shp(path):
    # deleteShapeFile
    os.remove(path)
    for ext in ['dbf', 'prj', 'qpj', 'shx']:
        os.remove(path[0:-3] + ext)


# function to add tolerance (deal with OSM and other decimal precision issues)
def keep_decimals(number, number_decimals):
    integer_part = abs(int(number))
    decimal_part = str(abs(int((number - integer_part) * (10 ** number_decimals))))
    if len(decimal_part) < number_decimals:
        zeros = str(0) * int((number_decimals - len(decimal_part)))
        decimal_part = zeros + decimal_part
    decimal = (str(integer_part) + '.' + decimal_part[0:number_decimals])
    if number < 0:
        decimal = ('-' + str(integer_part) + '.' + decimal_part[0:number_decimals])
    return decimal


def keep_decimals_string(string, number_decimals):
    integer_part = string.split(".")[0]
    decimal_part = string.split(".")[1][0:number_decimals]
    if len(decimal_part) < number_decimals:
        zeros = str(0) * int((number_decimals - len(decimal_part)))
        decimal_part = decimal_part + zeros
    decimal = integer_part + '.' + decimal_part
    return decimal


def read_shp_to_multi_graph(layer_name, tolerance=None, simplify=True):
    # 1. open shapefiles from directory/filename
    try:
        from osgeo import ogr
    except ImportError:
        raise ImportError("read_shp requires OGR: http://www.gdal.org/")

    # find if the table with the give table_name is a shapefile or a postgis file
    layer = getLayerByName(layer_name)
    path, provider_type = getLayerPath4ogr(layer)

    # TODO: push error message when path is empty/does not exist/connection with db does not exist
    if path == '':  # or not os.path.exists(path)
        return

    # construct a multi-graph
    net = nx.MultiGraph()
    lyr = ogr.Open(path)

    if provider_type == 'postgres':
        layer = [table for table in lyr if table.GetName() == layer_name][0]
        fields = [x.GetName() for x in layer.schema]
    elif provider_type in ('ogr', 'memory'):
        layer = lyr[0]
        fields = [x.GetName() for x in layer.schema]
    for f in layer:
        flddata = [f.GetField(f.GetFieldIndex(x)) for x in fields]
        g = f.geometry()
        attributes = dict(zip(fields, flddata))
        attributes["LayerName"] = lyr.GetName()
        # Note:  Using layer level geometry type
        if g.GetGeometryType() == ogr.wkbLineString:
            for edge in edges_from_line(g, attributes, tolerance, simplify):
                e1, e2, attr = edge
                net.add_edge(e1, e2, attr_dict=attr)
        elif g.GetGeometryType() == ogr.wkbMultiLineString:
            for i in range(g.GetGeometryCount()):
                geom_i = g.GetGeometryRef(i)
                for edge in edges_from_line(geom_i, attributes, tolerance, simplify):
                    e1, e2, attr = edge
                    net.add_edge(e1, e2, attr_dict=attr)
            # TODO: push message x features not included

    if provider_type == 'postgres':
        # destroy connection with db
        lyr.Destroy()
    elif provider_type == 'memory':
        # delete shapefile
        del_shp(path)

    return net


def edges_from_line(geom, attrs, tolerance=None, simplify=True):
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

    if simplify:
        edge_attrs = attrs.copy()
        last = geom.GetPointCount() - 1
        wkt = geom.ExportToWkt()
        if tolerance is not None:
            pt1 = geom.GetPoint_2D(0)
            pt2 = geom.GetPoint_2D(last)
            line = ogr.Geometry(ogr.wkbLineString)
            line.AddPoint_2D(snap_coord(pt1[0], tolerance), snap_coord(pt1[1], tolerance))
            line.AddPoint_2D(snap_coord(pt2[0], tolerance), snap_coord(pt2[1], tolerance))
            geom = line
            wkt = make_snapped_wkt(wkt, tolerance)
            last = 1
            del line
        edge_attrs["Wkt"] = wkt
        yield (geom.GetPoint_2D(0), geom.GetPoint_2D(last), edge_attrs)
    else:
        for i in range(0, geom.GetPointCount() - 1):
            pt1 = geom.GetPoint_2D(i)
            pt2 = geom.GetPoint_2D(i + 1)
            # TODO: construct segment geom
            if tolerance is not None:
                pt1 = (snap_coord(pt1[0], tolerance), snap_coord(pt1[1], tolerance))
                pt2 = (snap_coord(pt2[0], tolerance), snap_coord(pt2[1], tolerance))
            segment = ogr.Geometry(ogr.wkbLineString)
            segment.AddPoint_2D(pt1[0], pt1[1])
            segment.AddPoint_2D(pt2[0], pt2[1])
            edge_attrs = attrs.copy()
            edge_attrs["Wkt"] = segment.ExportToWkt()
            del segment
            yield (pt1, pt2, edge_attrs)


def snap_coord(coord, tolerance):
    return int(coord * (10 ** tolerance)) * (10**(tolerance - 2*tolerance))


def vertices_from_wkt(wkt):
    nums = [i for x in wkt[11:-1:].split(',') for i in x[1::].split(' ')]
    coords = zip(*[iter(nums)] * 2)
    for vertex in coords:
        yield vertex

def make_snapped_wkt(wkt, number_decimals):
    snapped_wkt = 'LINESTRING( '
    for i in vertices_from_wkt(wkt):
        new_vertex = str(keep_decimals_string(i[0], number_decimals)) + ' ' + str(
            keep_decimals_string(i[1], number_decimals))
        snapped_wkt += str(new_vertex) + ', '
    return snapped_wkt[0:-2] + ')'



