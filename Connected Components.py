import networkx as nx
nx

Main=iface.mapCanvas().currentLayer()
Main
G=nx.Graph()

nodes=[]
for f in Main.getFeatures():
    f_geom=f.geometry()
    id=f.attribute('id')
    print id
    p0=f_geom.asPolyline()[0]
    p1=f_geom.asPolyline()[1]
    G.add_edge(p0,p1,{'fid':id})
    if p0 in nodes:
        print 'already in'
    else:
        G.add_node(p0)
        nodes.append(p0)
    if p1 in nodes:
        print 'already in'
    else:
        G.add_node(p1)
        nodes.append(p1)

G.__len__()
G.size()

list(G.edges_iter(data='fid'))

Dual_G=nx.Graph()
for e in G.edges_iter(data='fid'):
    print e[2]
    Dual_G.add_node(e[2])

for n in Dual_G.nodes():
    print n

for i,j in G.adjacency_iter():
    print i,j
    if len(j)==2:
        values=[]
        for k,v in j.items():
            values.append(v['fid'])
        print values
        Dual_G.add_edge(values[0],values[1],data=None)

list(Dual_G.edges_iter())

from networkx.algorithms.components.connected import connected_components

for i in connected_components(Dual_G):
	print i
#lines with three connections have been included, breaks at intresections
#set also include single edges