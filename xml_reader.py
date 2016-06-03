import xml.etree.cElementTree as et

tree = et.parse('/Users/joe/Desktop/TfL_Santander Cycles availability.xml')

root = tree.getroot()

from qgis.core import *
from PyQt4.QtCore import QVariant

Points = QgsVectorLayer ( 'Point', 'Points', "memory")
Points.startEditing()

pr=Points.dataProvider()
pr.addAttributes([QgsField("name", QVariant.String), QgsField("id",  QVariant.Int), QgsField("long",  QVariant.Double), QgsField("lat",QVariant.Double)])

Points.commitChanges()

#You have to commit changes to the vector layer for using pedingFileds() method. Otherwise it will return an empty list
fields=Points.pendingFields()

Points.startEditing()

for station in root.findall('station'):
    id= station.find('id').text
    name = station.find('name').text
    lat = station.find ('lat').text
    long = station.find ('long').text
    station=QgsFeature()
    station.setGeometry( QgsGeometry.fromPoint(QgsPoint(float(long),float(lat))))
    station.setFields( fields, True)
    station['id']= int(id)
    station['name']=str(name)
    station['lat']=float(lat)
    station['long']=float(long)
    Points.addFeatures ([station])

Points.commitChanges()
QgsMapLayerRegistry.instance().addMapLayer(Points)