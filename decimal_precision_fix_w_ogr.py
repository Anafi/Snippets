def number_power(number,tolerance):
    return (int(number*(10**tolerance)))*(10**(tolerance - (int(2)*tolerance)))

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
        copied_layer = copy_shp(layer,path)
    return path, provider_type

import osgeo.ogr as ogr
import osr


layer=iface.mapCanvas().currentLayer()
path, pr = getLayerPath4ogr(layer)

data_source_input = ogr.Open(path)
input_layer = data_source_input.GetLayer(0)
input_layerDefinition = input_layer.GetLayerDefn()

fields = [x.GetName() for x in input_layer.schema]

# set up the shapefile driver
driver = ogr.GetDriverByName("ESRI Shapefile")
# create the data source
data_source = driver.CreateDataSource("C:\Users\I.Kolovou\Desktop\snapped_network.shp")
srs = osr.SpatialReference()
srs.ImportFromEPSG(32633)

# create the layer
snapped_layer = data_source.CreateLayer("C:\Users\I.Kolovou\Desktop\snapped_network.shp", srs, ogr.wkbLineString)

# Add the fields we're interested in
id_field = ogr.FieldDefn("id", ogr.OFTInteger)
snapped_layer.CreateField(id_field)
level_field = ogr.FieldDefn("level", ogr.OFTString)
snapped_layer.CreateField(level_field)
wkt_field = ogr.FieldDefn("wkt", ogr.OFTString)
wkt_field.SetWidth(250)
snapped_layer.CreateField(wkt_field)


for f in input_layer:
    flddata = [f.GetField(f.GetFieldIndex(x)) for x in fields]
    geom = f.geometry()
    snapped_feature = ogr.Feature(snapped_layer.GetLayerDefn())
    for ind,field_name in enumerate(fields):
        snapped_feature.SetField(field_name, flddata[ind])
    pt1 =geom.GetPoint_2D(0)
    pt2 =geom.GetPoint_2D(geom.GetPointCount() - 1)
    snapped_segment = ogr.Geometry(ogr.wkbLineString)
    snapped_segment.AddPoint_2D(pt1[0], pt1[1])
    snapped_segment.AddPoint_2D(pt2[0], pt2[1])
    snapped_feature.SetField("wkt", snapped_segment.ExportToWkt())
    snapped_feature.SetGeometry(snapped_segment)
    snapped_layer.CreateFeature(snapped_feature)
    snapped_feature.Destroy()

data_source.Destroy()
