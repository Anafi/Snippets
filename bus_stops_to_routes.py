# A script to recreate bus routes from tfl's bus stop locations & os road network(network should not contain polylines)
# The script finds the closest line to every stop
# It groups all stops according to route and run and sorts the stops based on sequence.
# Then it makes pairs between segments of stops per route and run and find shortest path between them
# TO DO: find based on street name and if names do not match closest neighbour
# TO DO: for shortest_path use a graph that has a cost of primary and secondary routes

# load dependencies
import math
from qgis.core import *

# define line layer of your network (n) and point layer representing the bus stops (p)
n = iface.mapCanvas().currentLayer()
p = iface.mapCanvas().currentLayer()

# create spatial index for features in line layer
provider = n.dataProvider()
spIndex = QgsSpatialIndex()  # create spatial index object
feat = QgsFeature()
fit = provider.getFeatures()  # gets all features in layer
# insert features to index
while fit.nextFeature(feat):
    spIndex.insertFeature(feat)

# find four nearest lines to a point
p_to_lines = {}  # { point_id: closest line neighbour segment id}
for i in p.getFeatures():
    nearestIds = spIndex.nearestNeighbor(QgsPoint(i.geometry().asPoint()),1)
    p_to_lines[i.id()] = nearestIds


# filter neighbours based on distance for k, v in p_to_lines.items():


def distance_point_to_line(point_feat, line_feat):
    magnitude = math.hypot( abs(line_endpoints[line_feat][0][0] - line_endpoints[line_feat][1][0]), abs(line_endpoints[line_feat][0][1] - line_endpoints[line_feat][1][1]))
    u = ((points_coord[point_feat][0] - line_endpoints[line_feat][0][0]) * (line_endpoints[line_feat][1][0] - line_endpoints[line_feat][0][0]) + (points_coord[point_feat][1] - line_endpoints[line_feat][0][1]) * (line_endpoints[line_feat][1][1] - line_endpoints[line_feat][0][1])) / (magnitude)
    ix = line_endpoints[line_feat][0][0] + u * (line_endpoints[line_feat][1][0] - line_endpoints[line_feat][0][0])
    iy = line_endpoints[line_feat][0][1] + u * (line_endpoints[line_feat][1][1] - line_endpoints[line_feat][0][1])
    distance = math.hypot( abs(ix-points_coord[point_feat][0]), abs(iy-points_coord[point_feat][1]))
    return distance

# save all line feature endpoints with ids
# save all point feature x,y coordinates
line_endpoints = {feat.id(): [feat.geometry().asPolyline()[0], feat.geometry().asPolyline()[-1]] for feat in n.getFeatures()}
points_coord = {feat.id(): feat.geometry().asPoint() for feat in p.getFeatures()}


for k, v in p_to_lines.items():
    if len(v) == 1:
        pass
    else:
        distance = 10000000000
        closest_line = None
        for line in v:
            if ((abs(line_endpoints[line][0][0])< abs(points_coord[k][0]) and abs(line_endpoints[line][1][0])> abs(points_coord[k][0])) or (abs(line_endpoints[line][0][0])> abs(points_coord[k][0]) and abs(line_endpoints[line][1][0])< abs(points_coord[k][0]))) and distance_point_to_line(k,line) < distance:
                closest_line = line
                distance = distance_point_to_line(k,line)
        p_to_lines[k] = [closest_line]


lines=[]
for k, v in p_to_lines.items():
    lines.append(v[0])

n.select(lines)