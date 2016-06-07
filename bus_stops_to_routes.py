# A script to recreate bus routes from tfl's bus stop locations & os road network(network should not contain polylines)
# The script finds the closest line to every stop
# It groups all stops according to route and run and sorts the stops based on sequence.
# Then it makes pairs between segments of stops per route and run and find shortest path between them
# TO DO: find based on street name and if names do not match closest neighbour
# TO DO: for shortest_path use a graph that has a cost of primary and secondary routes

# load dependencies
import math
from qgis.core import *
from itertools import groupby
from operator import itemgetter
import networkx as nx

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
    nearestIds = spIndex.nearestNeighbor(QgsPoint(i.geometry().asPoint()), 4)
    p_to_lines[i.id()] = nearestIds

# filter neighbours based on distance for k, v in p_to_lines.items():


def distance_point_to_line(point_feat, line_feat):
    magnitude = math.hypot(abs(line_endpoints[line_feat][0][0] - line_endpoints[line_feat][1][0]), abs(line_endpoints[line_feat][0][1] - line_endpoints[line_feat][1][1]))
    u = ((points_coord[point_feat][0] - line_endpoints[line_feat][0][0]) * (line_endpoints[line_feat][1][0] - line_endpoints[line_feat][0][0]) + (points_coord[point_feat][1] - line_endpoints[line_feat][0][1]) * (line_endpoints[line_feat][1][1] - line_endpoints[line_feat][0][1])) / (math.pow(magnitude,2))
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
    lines_between = []

    for line in v:
        # find angle of point- bus stop (O) and endpoint of lines ( A, B)
        OA = math.hypot((line_endpoints[line][0][0] - points_coord[k][0]),(line_endpoints[line][0][1] - points_coord[k][1]))
        OB = math.hypot((line_endpoints[line][1][0] - points_coord[k][0]),(line_endpoints[line][1][1] - points_coord[k][1]))
        AB = math.hypot((line_endpoints[line][0][0] - line_endpoints[line][1][0]),(line_endpoints[line][0][1] - line_endpoints[line][1][1]))
        OAB = math.degrees(math.acos((math.pow(OA,2) + math.pow(AB,2) - math.pow(OB,2))/(2*OA*AB)))
        OBA = math.degrees(math.acos((math.pow(OB,2) + math.pow(AB,2) - math.pow(OA,2))/(2*OB*AB)))
        if OAB <= 90 and OBA <= 90:
            lines_between.append(line)
    distances = []
    for l in lines_between:
        distances.append(distance_point_to_line(k, l))
    sorted_lines = [x for (y, x) in sorted(zip(distances, lines_between))]
    if len(sorted_lines) == 0:
        closest_line = v[0]
    else:
        closest_line = sorted_lines[0]
    if len(sorted_lines) > 1:
        if (line_class[sorted_lines[1]] == u'A Road' or line_class[sorted_lines[1]]== u'B Road') and not (line_class[sorted_lines[0]] == u'A Road' or line_class[sorted_lines[0]]== u'B Road') :
            closest_line = sorted_lines[1]
    p_to_lines[k] = [closest_line]


lines = []
for k, v in p_to_lines.items():
    lines.append(v[0])

n.select(lines)

################################################################################################
# group by route and run
bus_routes=[]
for point in p.getFeatures():
    route = point.attributes()[1]
    seq = int(point.attributes()[3])
    run = int(point.attributes()[2])
    bus_routes.append([point.id(), route, run, seq])

Routes = {}
for route, iter in groupby(bus_routes, itemgetter(1)):
    list = []
    for i in iter:
        list.append(i)
    for j, v in groupby(list,itemgetter(2)):
        list_2 = []
        for k in v:
            list_2.append(k)
        Routes[route, j] = list_2

for i, v in Routes.items():
    v.sort(key=itemgetter(3))

# find pairs of sorted grouped line segments
pairs = []
for k, v in Routes.items():
    list = []
    for i in v:
        list.append(i[0])
    for v, w in zip(list[:-1], list[1:]):
        pairs.append([v, w])

seg_pairs = []
for i in pairs:
    seg_pair = p_to_lines[i[0]] + p_to_lines[i[1]]
    seg_pairs.append(seg_pair)

D = {}
for i in n.getFeatures():
    D[i.id()] = [(i.geometry().asPolyline()[0][0], i.geometry().asPolyline()[0][1]), (i.geometry().asPolyline()[-1][0], i.geometry().asPolyline()[-1][1]) ]

point_pairs = []
for i in seg_pairs:
    point_pairs.append([D[i[0]][0],D[i[1]][0]])


G = nx.Graph()
for f in n.getFeatures():
    f_geom = f.geometry()
    id = f.id()
    p0 = (f_geom.asPolyline()[0][0], f_geom.asPolyline()[0][1])
    p1 = (f_geom.asPolyline()[-1][0], f_geom.asPolyline()[-1][1])
    G.add_edge(p0, p1, {'fid': id})

# TO DO: add cost to the network based on class type
paths = []
for i in point_pairs:
    paths.append(nx.shortest_path(G, source=i[0], target=i[1]))

endpoints_to_keep = []
for path in paths:
    for i in path:
        if i not in endpoints_to_keep:
            endpoints_to_keep.append(i)

bus_route_paths = []
for k, v in D.items():
    if v[0] in endpoints_to_keep and v[1] in endpoints_to_keep:
        if k not in bus_route_paths:
            bus_route_paths.append(k)

for k, v in p_to_lines.items():
    if v[0] not in bus_route_paths:
        bus_route_paths.append(v[0])

n.select(bus_route_paths)