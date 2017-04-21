# imports
execfile(u'C:/Users/I.Kolovou/Desktop/sGraph/dual_graph.py'.encode('utf-8'))
execfile(u'C:/Users/I.Kolovou/Desktop/sGraph/generalFunctions.py'.encode('utf-8'))
execfile(u'C:/Users/I.Kolovou/Desktop/sGraph/plFunctions.py'.encode('utf-8'))
execfile(u'C:/Users/I.Kolovou/Desktop/sGraph/primal_graph.py'.encode('utf-8'))
execfile(u'C:/Users/I.Kolovou/Desktop/sGraph/shpFunctions.py'.encode('utf-8'))
execfile(u'C:/Users/I.Kolovou/Desktop/sGraph/utilityFunctions.py'.encode('utf-8'))

execfile(u'C:/Users/I.Kolovou/Documents/GitHub/Snippets/vector_to_dual_continuity_lines.py'.encode('mbcs'))

from PyQt4.QtCore import QVariant
qgsflds_types = {u'Real': QVariant.Double , u'String': QVariant.String}

#------------------- CHANGES

#layer_name = 'MK_polyline_model'
layer_name = 'MK_polyline_model'
csv_path = 'P:/2240_InnovateUK_Integrated_City_Modelling/2240_Project_Work/2240_Axial/2240_Composite_Model/nx_processing_MK/nxCh_pl.csv'
network_path = r'P:/2240_InnovateUK_Integrated_City_Modelling/2240_Project_Work/2240_Axial/2240_Composite_Model/nx_processing_MK/MK_polyline_model.shp'
# ADD new feature id column
# id column should be feature id)
base_id = 'feature_id'

# overwrite function
# the wkt representation may differ in other systems/ QGIS versions

def vertices_from_wkt(wkt):
    # the wkt representation may differ in other systems/ QGIS versions
    # TODO: check
    nums = [i for x in wkt[12:-1:].split(', ') for i in x.split(' ')]
    coords = zip(*[iter(nums)] * 2)
    for vertex in coords:
        yield vertex

def make_snapped_wkt(wkt, number_decimals):
    # TODO: check in different system if '(' is included
    snapped_wkt = 'LINESTRING ('
    for i in vertices_from_wkt(wkt):
        new_vertex = str(keep_decimals_string(i[0], number_decimals)) + ' ' + str(
            keep_decimals_string(i[1], number_decimals))
        snapped_wkt += str(new_vertex) + ', '
    return snapped_wkt[0:-2] + ')'

transformation_type = 'shp_to_pgr'

parameters = {'layer_name': layer_name, 'tolerance': 3, 'simplify': True, 'id_column': base_id}
primal_graph = transformer(parameters, transformation_type).result

any_primal_graph = prGraph(primal_graph, base_id)
print any_primal_graph.obj.size()
print any_primal_graph.obj.__len__()

dg = graph_to_dual(any_primal_graph.obj, base_id, inter_to_inter=False)
dual_to_shp(network_path,dg,True)

# update cost on dual graph
dual_name = 'dual_graph_edges'

dual_shp = getLayerByName(dual_name)
costs_dict = {(i.attributes()[1], i.attributes()[2]): i.attributes()[6] for i in dual_shp.getFeatures()}
dg_w_cost = nx.MultiGraph()
for i in dg.edges(data=True):
    dg_w_cost.add_edge(i[0], i[1], cost = costs_dict[(i[0], i[1])])


# process dual_graph
from networkx import betweenness_centrality
choice = nx.betweenness_centrality(dg_w_cost, k=None, normalized=False, weight='cost', endpoints=False, seed=None)

# TODO: test local measures
# betweenness_centrality_subset(G, sources, targets, normalized=False, weight=None)

# push the results back to network
import csv

with open(csv_path, 'wb') as csv_file:
    writer = csv.writer(csv_file)
    for key, value in choice.items():
       writer.writerow([key, value])
