from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *

Athens_allRoads = iface.mapCanvas().currentLayer()

expr_Primary = QgsExpression("\"type\"= 'primary'" or "\"type\"='primary_link'")

provider = Athens_allRoads.dataProvider()

primary_writer = QgsVectorFileWriter ("/Users/joe/Documents/2015_Localities/Primary_network.shp", "UTF-8" , provider.fields() ,provider.geometryType(), provider.crs() , "ESRI Shapefile")

if primary_writer.hasError() != QgsVectorFileWriter.NoError:
    print "Error when creating shapefile: ",  primary_writer.errorMessage()

primary_elem= QgsFeature()

for elem in Athens_allRoads.getFeatures (QgsFeatureRequest( expr_Primary)):
    primary_elem.setGeometry(elem.geometry())
    primary_elem.setAttributes(elem.attributes())
    primary_writer.addFeature(primary_elem)

del primary_writer