__author__ = 'joe'
import xml.etree.cElementTree as et

tree = et.parse('/Users/joe/Desktop/TfL_Santander Cycles availability.xml')

root = tree.getroot()

from qgis.core import *
from PyQt4.QtCore import QVariant

Points = QgsVectorLayer ( 'Point', 'Points', "memory")
Points.startEditing()

Points.addAttributes( [ QgsField("name", QVariant.String), QgsField("id",  QVariant.Int), QgsField("long",  QVariant.Double), QgsField("lat",QVariant.Double)])


"""for station in root.findall('station'):
	id= station.find('id').text
	name = station.find('name').text
	long = station.find ('long').text
	lat = station.find ('lat').text
	station=QgsFeature()
	station.setGeometry( QgsGeometry.fromPoint(QgsPoint(float(lat),float(long))))
	station.setAttribute ({0: QVariant(name), 1:QVariant(int(id)) , 2:QVariant(float(long)) , 3:QVariant(float(lat)) })
	pr.addFeatures ([station])

Points.commitChanges()
QgsMapLayerRegistry.instance().addMapLayer(Points)"""


for station in root.findall('station'):
	id= station.find('id').text
	name = station.find('name').text
	lat = station.find ('lat').text
	long = station.find ('long').text
	station=QgsFeature()
	station.setGeometry( QgsGeometry.fromPoint(QgsPoint(float(long),float(lat))))
	fields=pr.fields()
	station.setFields( fields, True)
	station['id']= int(id)
	station['name']=str(name)
	station['lat']=float(lat)
	station['long']=float(long)
	Points.addFeatures ([station])

Points.commitChanges()
QgsMapLayerRegistry.instance().addMapLayer(Points)