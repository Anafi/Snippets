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
    nearestIds = spIndex.nearestNeighbor(QgsPoint(i.geometry().asPoint()), 2)
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
# save all line feature class attributes
line_endpoints = {feat.id(): [feat.geometry().asPolyline()[0], feat.geometry().asPolyline()[-1]] for feat in n.getFeatures()}
points_coord = {feat.id(): feat.geometry().asPoint() for feat in p.getFeatures()}
line_class = {feat.id(): feat.attributes()[2] for feat in n.getFeatures()}

# filter lines, where a bus stop is between their endpoints
# filter two closest lines and select the one that is on primary network
# filter lines that are on the primary network if any

for k, v in p_to_lines.items():
    filtered_lines = []
    distances = []
    for line in v:
        distances.append(distance_point_to_line(k, line))
    sorted_lines = [x for (y, x) in sorted(zip(distances, filtered_lines))]
    for sorted_line in

    two_closest_lines = [sorted_lines[0] + sorted_lines[1]]

        # find angle of point- bus stop (O) and endpoint of lines ( A, B)
        OA = math.hypot((line_endpoints[line][0][0] - points_coord[k][0]),(line_endpoints[line][0][1] - points_coord[k][1]))
        OB = math.hypot((line_endpoints[line][1][0] - points_coord[k][0]),(line_endpoints[line][1][1] - points_coord[k][1]))
        AB = math.hypot((line_endpoints[line][0][0] - line_endpoints[line][1][0]),(line_endpoints[line][0][1] - line_endpoints[line][1][1]))
        OAB = math.degrees(math.acos((OA**2 + AB**2 - OB**2)/(2*OA*AB)))
        OBA = math.degrees(math.acos((OB**2 + AB**2 - OA**2)/(2*OB*AB)))
        if OAB <= 90 and OBA <= 90:
            filtered_lines.append(line)

    for filtered_line in filtered_lines:
        distances.append(distance_point_to_line(k,line))


    if line_class[two_closest_lines[1]] == u'A Road' or line_class[two_closest_lines[1]] == u'B Road':
        closest_line = two_closest_lines[1]
    else:
        closest_line = two_closest_lines[0]
    p_to_lines[k] = [closest_line]


lines = []
for k, v in p_to_lines.items():
    lines.append(v[0])

n.select(lines)