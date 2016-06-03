__author__ = 'joe'

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *

Intersections = iface.mapCanvas().currentLayer()
Intersections

Foreground = iface.mapCanvas().currentLayer()
Foreground

#from shapely.geometry import Point

#for line in Foreground:
#   for point in len(line.coords):
#       if Point(line['geometry']['coordinates'][0]), Point(line['geometry']['coordinates'][-1])

#create a list of all endpoints of the Foreground network
for f in Foreground.getFeatures():
	Endpoints=f.geometry().asPolyline()
	for i in Endpoints:
		i_x=i.x
		i_y=i.y
		endpoint= [i_x,i_y]
		mega_list.append(i)

mega_list
#returns a list of tuples of all endpoints

Intersections.startEditing()
for f in Intersections.getFeatures():
    point=f.geometry().asPoint()
    if point in mega_list:
        #print True
        fid = f.id()
        Intersections.deleteFeature(fid)

Intersections.commitChanges()

#list_x= [ x[0] for x in mega_list]
#print list_x[1]

#list_y=[y[1] for y in mega_list]
#print list_y[1]
