#This is a tool for simplyfing an openstreet map

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *

"""Step 1: separate foreground from background network"""

#select current layer (you can also try to load a Vector layer by its path)
Athens_allRoads = iface.mapCanvas().currentLayer()

#two expressions for Foreground and Background
expr_Foreground = QgsExpression("type= 'primary' OR type='primary_link' OR type = 'motorway' OR type= 'motorway_link' OR type= 'secondary' OR type= 'secondary_link' OR type= 'trunk' OR type= 'trunk_link'")
expr_Background = QgsExpression("type=tertiary or type=tertiary_link or type= 'bridge' OR type='footway' OR type = 'living_street' OR type= 'path' OR type= 'pedestrian' OR type= 'residential' OR type= 'road' OR type= 'service' OR type= 'steps' OR type= 'track' OR type= 'unclassified'")

#create two writers to write the new vector layers
provider = Athens_allRoads.dataProvider()
Foreground_writer = QgsVectorFileWriter ("/Users/joe/Documents/2015_Localities/Foreground_network.shp", "UTF-8", provider.fields() ,provider.geometryType(), provider.crs() , "ESRI Shapefile")
Background_writer = QgsVectorFileWriter ("/Users/joe/Documents/2015_Localities/Background_network.shp", "UTF-8", provider.fields() ,provider.geometryType(), provider.crs() , "ESRI Shapefile")

if Foreground_writer.hasError() != QgsVectorFileWriter.NoError:
    print "Error when creating shapefile: ",  Foreground_writer.errorMessage()
if Background_writer.hasError() != QgsVectorFileWriter.NoError:
    print "Error when creating shapefile: ",  Background_writer.errorMessage()

#get features based on the queries and add them to the new layers
#avoid printing True (processing time)
Foreground_elem= QgsFeature()

for elem in Athens_allRoads.getFeatures (QgsFeatureRequest(expr_Foreground)):
    Foreground_elem.setGeometry(elem.geometry())
    Foreground_elem.setAttributes(elem.attributes())
    Foreground_writer.addFeature(Foreground_elem)

del Foreground_writer

Background_elem= QgsFeature()

for elem in Athens_allRoads.getFeatures (QgsFeatureRequest(expr_Background)):
    Background_elem.setGeometry(elem.geometry())
    Background_elem.setAttributes(elem.attributes())
    Background_writer.addFeature(Background_elem)

del Background_writer

#add the two new layers to the mapCanvas
Foreground=QgsVectorLayer ("/Users/joe/Documents/2015_Localities/Foreground_network.shp", 'Foreground', 'ogr')
Background=QgsVectorLayer ("/Users/joe/Documents/2015_Localities/Background_network.shp", 'Background', 'ogr')

QgsMapLayerRegistry.instance().addMapLayers([Foreground,Background])
iface.mapCanvas().refresh()

"""Step 2: Integrate multiple lines into one for the foreground and background network"""
#make dictionary with same names, include NULL values
#add new field 'id', and rowid all features, including NULL values
#double entries first and last feature
#NULL values are being multiplied
#Make the second loop work with expr_name = QgsExpression("\"name\" == fname")





####################### Step 3: Extend background to foreground network

####################### Step 4: Merge two networks into one spatial models

####################### Step 5: Simplify network by preserving its topology
#Simplification should include:
#1. remove vertices
#2. remove small segments

####################### Step 6: Generate unlinks in intersections

####################### Step 7: Clean the model
#1. remove lines with length = 0
#2. remove invalid geometry
#3. remove isolated lines
#4. snap lines