# imports
execfile(u'C:/Users/I.Kolovou/Documents/GitHub/Rcl-topology-cleaner/geometryFunctions/wktFunctions.py'.encode('utf-8'))
execfile(u'C:/Users/I.Kolovou/Documents/GitHub/Rcl-topology-cleaner/otherFunctions/utilityFunctions.py'.encode('utf-8'))
execfile(u'C:/Users/I.Kolovou/Documents/GitHub/Rcl-topology-cleaner/sGraphFunctions/analyser.py'.encode('utf-8'))
execfile(u'C:/Users/I.Kolovou/Documents/GitHub/Rcl-topology-cleaner/otherFunctions/shpFunctions.py'.encode('utf-8'))
execfile(u'C:/Users/I.Kolovou/Documents/GitHub/Rcl-topology-cleaner/sGrpah/sGraph.py'.encode('utf-8'))
execfile(u'C:/Users/I.Kolovou/Documents/GitHub/Rcl-topology-cleaner/sGrpah/prGraph.py'.encode('utf-8'))
execfile(u'C:/Users/I.Kolovou/Documents/GitHub/Rcl-topology-cleaner/geometryFunctions/plFunctions.py'.encode('utf-8'))
execfile(u'C:/Users/I.Kolovou/Documents/GitHub/Rcl-topology-cleaner/otherFunctions/generalFunctions.py'.encode('utf-8'))
execfile(u'C:/Users/I.Kolovou/Documents/GitHub/Rcl-topology-cleaner/sGrpah/fMap.py'.encode('utf-8'))
execfile(u'C:/Users/I.Kolovou/Documents/GitHub/Rcl-topology-cleaner/sGrpah/dlGraph.py'.encode('utf-8'))
execfile(u'C:/Users/I.Kolovou/Documents/GitHub/Rcl-topology-cleaner/sGraphFunctions/transformer.py'.encode('utf-8'))
execfile(u'C:/Users/I.Kolovou/Documents/GitHub/Rcl-topology-cleaner/sGraphFunctions/cleaner.py'.encode('utf-8'))

from PyQt4.QtCore import QVariant
qgsflds_types = {u'Real': QVariant.Double , u'String': QVariant.String}

layer_name = 'MK_polyline_model'

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
base_id = 'id'
parameters = {'layer_name': layer_name, 'tolerance': 3, 'simplify': True, 'id_column': base_id}
primal_graph = transformer(parameters, transformation_type).result

any_primal_graph = prGraph(primal_graph, base_id)
print any_primal_graph.obj.size()
print any_primal_graph.obj.__len__()

#transformation_type ='prg_to_dlgr'
#parameters = {'prGraph': any_primal_graph, 'break_at_intersections': False,'id_column': base_id}
#dual_g = dlGraph(transformer(parameters,transformation_type).result,parameters['id_column'])
#print dual_g.obj.size()
#print dual_g.obj.__len__()

# match qgs fields to primal graph fields
#prflds = any_primal_graph.get_fields()
#flds = [QgsField(i, qgsflds_types[u'String']) for i in prflds[0]]

# transform primal graph to qfeatures
#transformation_type = 'prg_to_qf'
#parameters = {'prGraph': any_primal_graph, 'id_column': base_id, 'fields': flds, 'count':0}
#base_id = 'id'
# no fields set up, no fid in the result of the transformation
#qf = fMap(transformer(parameters, transformation_type).result, parameters['count'])
#print qf.obj[0].id(), qf.obj[1].id()

#transformation_type = 'dlgr_to_qf'
#attr_index = 4
#parameters = {'fMap': qf,'attr_index': attr_index, 'dlGraph': dual_g, 'id_column': base_id, 'count':0}
#dl_qf = fMap(transformer(parameters, transformation_type).result, parameters['count'])

execfile(u'C:/Users/I.Kolovou/Desktop/python_code/vector_to_dual_continuity_lines.py'.encode('mbcs'))
dg = graph_to_dual(any_primal_graph.obj, 'id', inter_to_inter=False)
network_path = r'P:/2240_InnovateUK_Integrated_City_Modelling/2240_Project_Work/2240_Axial/2240_Composite_Model/MK_polyline_model.shp'
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
choice = nx.betweenness_centrality(dg_w_cost, k=None, normalized=True, weight='cost', endpoints=False, seed=None)

# push the results back to network

with open('C:/Users/I.Kolovou/Desktop/test.csv', 'wb') as csv_file:
    writer = csv.writer(csv_file)
    for key, value in choice.items():
       writer.writerow([key, value])
