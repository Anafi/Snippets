
# network
n = iface.mapCanvas().currentLayer()

from qgis.core import *
from PyQt4.QtCore import QVariant
import math

#add a column in the network_input file with feature ID
n.startEditing()
n.dataProvider().addAttributes([QgsField("wkt", QVariant.String)])
n.commitChanges()

fieldIdx = n.dataProvider().fields().indexFromName("wkt")

updateMap_geom = {}

def digit_sum(n):
    n = abs(n)
    total = 0
    while n >= 1:
        total += (n % 10)
        n = n // 10
    return total

def get_two_decimals(number):
    d = number - int(number)
    two_decimals = float(str(d)[0:4])
    new_number = int(number) + two_decimals
    return new_number

# method 1 by rounding up (you need to v.clean-snap afterwards)
for f in n.getFeatures():
    fid = f.id()
    start_point_x = round(f.geometry().asPolyline()[0][0], 0)
    start_point_y = round(f.geometry().asPolyline()[0][1], 0)
    end_point_x = round(f.geometry().asPolyline()[1][0], 0)
    end_point_y = round(f.geometry().asPolyline()[1][1], 0)
    wkt_geom = 'LineString ('+str(start_point_x)+' '+str(start_point_y)+', '+str(end_point_x)+' '+str(end_point_y)+')'
    updateMap_geom[fid] = {fieldIdx: wkt_geom}

# method 2 by keeping the two decimals (still number is float)
for f in n.getFeatures():
    fid = f.id()
    start_point_x = get_two_decimals(f.geometry().asPolyline()[0][0])
    start_point_y = get_two_decimals(f.geometry().asPolyline()[0][1])
    end_point_x = get_two_decimals(f.geometry().asPolyline()[1][0])
    end_point_y = get_two_decimals(f.geometry().asPolyline()[1][1])
    wkt_geom = 'LineString ('+str(start_point_x)+' '+str(start_point_y)+', '+str(end_point_x)+' '+str(end_point_y)+')'
    updateMap_geom[fid] = {fieldIdx: wkt_geom}

# method 3 by converting to integers
for f in n.getFeatures():
    fid = f.id()
    start_point_x = int(f.geometry().asPolyline()[0][0])
    start_point_y = int(f.geometry().asPolyline()[0][1])
    end_point_x = int(f.geometry().asPolyline()[1][0])
    end_point_y = int(f.geometry().asPolyline()[1][1])
    wkt_geom = 'LineString ('+str(start_point_x)+' '+str(start_point_y)+', '+str(end_point_x)+' '+str(end_point_y)+')'
    updateMap_geom[fid] = {fieldIdx: wkt_geom}

n.dataProvider().changeAttributeValues(updateMap_geom)


