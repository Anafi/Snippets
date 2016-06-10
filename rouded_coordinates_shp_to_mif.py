
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

# find the maximum and the minimum number of digits for x-s and y-s
max_digit_x = 0
min_digit_x = 100000000
max_digit_y = 0
min_digit_y = 100000000


def digit_sum(n):
    n = abs(n)
    total = 0
    while n >= 1:
        total += (n % 10)
        n = n // 10
    return total


# digit_start_x = digit_sum(f.geometry().asPolyline()[0][0])
# digit_end_x = digit_sum(f.geometry().asPolyline()[1][0])
# if digit_start_x > max_digit_x:
#    max_digit_x = digit_start_x
# if digit_end_x > max_digit_x:
#    max_digit_x = digit_end_x
# if digit_start_x < min_digit_x:
#    min_digit_x = digit_start_x
# if digit_end_x < min_digit_x:
#    min_digit_x = digit_end_x
# digit_start_y = digit_sum(f.geometry().asPolyline()[0][1])
# digit_end_y = digit_sum(f.geometry().asPolyline()[1][1])
# if digit_start_y > max_digit_y:
#    max_digit_y = digit_start_y
# if digit_end_y > max_digit_y:
#    max_digit_y = digit_end_y
# if digit_start_y < min_digit_y:
#    min_digit_y = digit_start_y
# if digit_end_y < min_digit_y:
#    min_digit_y = digit_end_y

for f in n.getFeatures():
    fid=f.id()
    start_point_x = round(f.geometry().asPolyline()[0][0], 0)
    # if len(str(math.modf(start_point_x)[0])) == 4:
    #    start_point_x = str(start_point_x)+'0'
    start_point_y = round(f.geometry().asPolyline()[0][1], 0)
    # if len(str(math.modf(start_point_y)[0])) == 4:
    #    start_point_y = str(start_point_y) + '0'
    end_point_x = round(f.geometry().asPolyline()[1][0], 0)
    # if len(str(math.modf(end_point_x)[0])) == 4:
    #    end_point_x = str(end_point_x) + '0'
    end_point_y = round(f.geometry().asPolyline()[1][1], 0)
    # if len(str(math.modf(end_point_y)[0])) == 4:
    #    start_end_y = str(end_point_y) + '0'
    wkt_geom = 'LineString ('+str(start_point_x)+' '+str(start_point_y)+', '+str(end_point_x)+' '+str(end_point_y)+')'
    updateMap_geom[fid] = {fieldIdx: wkt_geom}


n.dataProvider().changeAttributeValues( updateMap_geom )


