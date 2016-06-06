

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

for f in n.getFeatures():
    fid=f.id()
    start_point_x = round(f.geometry().asPolyline()[0][0], 3)
    if len(str(math.modf(start_point_x)[0])) == 4:
        start_point_x = str(start_point_x)+'0'
    start_point_y = round(f.geometry().asPolyline()[0][1], 0)
    if len(str(math.modf(start_point_y)[0])) == 4:
        start_point_y = str(start_point_y) + '0'
    end_point_x = round(f.geometry().asPolyline()[1][0], 0)
    if len(str(math.modf(end_point_x)[0])) == 4:
        end_point_x = str(end_point_x) + '0'
    end_point_y = round(f.geometry().asPolyline()[1][1], 0)
    if len(str(math.modf(end_point_y)[0])) == 4:
        start_end_y = str(end_point_y) + '0'
    wkt_geom = 'LineString ('+str(start_point_x)+' '+str(start_point_y)+', '+str(end_point_x)+' '+str(end_point_y)+')'
    updateMap_geom[fid] = {fieldIdx: wkt_geom}


n.dataProvider().changeAttributeValues( updateMap_geom )

