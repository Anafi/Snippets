#This is a tool for simplyfing an openstreet map

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *

"""Step 1: separate foreground from background network"""

#select current layer (you can also try to load a Vector layer by its path)
Athens_allRoads = iface.mapCanvas().currentLayer()

#two expressions for Foreground and Background
expr_Foreground = QgsExpression("type= 'primary' OR type='primary_link' OR type = 'motorway' OR type= 'motorway_link' OR type= 'secondary' OR type= 'secondary_link' OR type= 'trunk' OR type= 'trunk_link'")
expr_Background = QgsExpression("type=tertiary or type=tertiary_link or type= 'bridge' OR type='footway' OR type = 'living_street' OR type= 'path' OR type= 'pedestrian' OR type= 'residential' OR type= 'road' OR type= 'service' OR type= 'steps' OR type= 'track' OR type= 'unclassified'")

#create two writers to write the new vector layers
provider = Athens_allRoads.dataProvider()
Foreground_writer = QgsVectorFileWriter ("/Users/joe/Documents/2015_Localities/Foreground_network.shp", "UTF-8", provider.fields() ,provider.geometryType(), provider.crs() , "ESRI Shapefile")
Background_writer = QgsVectorFileWriter ("/Users/joe/Documents/2015_Localities/Background_network.shp", "UTF-8", provider.fields() ,provider.geometryType(), provider.crs() , "ESRI Shapefile")

if Foreground_writer.hasError() != QgsVectorFileWriter.NoError:
    print "Error when creating shapefile: ",  Foreground_writer.errorMessage()
if Background_writer.hasError() != QgsVectorFileWriter.NoError:
    print "Error when creating shapefile: ",  Background_writer.errorMessage()

#get features based on the queries and add them to the new layers
#avoid printing True (processing time)
Foreground_elem= QgsFeature()

for elem in Athens_allRoads.getFeatures (QgsFeatureRequest(expr_Foreground)):
    Foreground_elem.setGeometry(elem.geometry())
    Foreground_elem.setAttributes(elem.attributes())
    Foreground_writer.addFeature(Foreground_elem)

del Foreground_writer

Background_elem= QgsFeature()

for elem in Athens_allRoads.getFeatures (QgsFeatureRequest(expr_Background)):
    Background_elem.setGeometry(elem.geometry())
    Background_elem.setAttributes(elem.attributes())
    Background_writer.addFeature(Background_elem)

del Background_writer

#add the two new layers to the mapCanvas
Foreground=QgsVectorLayer ("/Users/joe/Documents/2015_Localities/Foreground_network.shp", 'Foreground', 'ogr')
Background=QgsVectorLayer ("/Users/joe/Documents/2015_Localities/Background_network.shp", 'Background', 'ogr')

QgsMapLayerRegistry.instance().addMapLayers([Foreground,Background])
iface.mapCanvas().refresh()

"""Step 2: Integrate multiple lines into one for the foreground and background network"""
""""""""""""""""""""""""""""""""""""""""""""""""""""""""
import networkx as nx
nx

#Main network does not contain primary_link, secondary_link, trunk_link
#Main network has been exploded
#Should main network be simplified??
Main=iface.mapCanvas().currentLayer()
Main

#make a graph out of the Main network (nodes=endpoints of lines, edges=lines)
G=nx.Graph()
nodes=[]

for f in Main.getFeatures():
    f_geom=f.geometry()
    id=f.attribute('id')
    #print id
    p0=f_geom.asPolyline()[0]
    p1=f_geom.asPolyline()[1]
    G.add_edge(p0,p1,{'fid':id})
    if p0 in nodes:
        pass
        #print 'already in'
    else:
        G.add_node(p0)
        nodes.append(p0)
    if p1 in nodes:
        pass
        #print 'already in'
    else:
        G.add_node(p1)
        nodes.append(p1)

G.__len__()
G.size()

list(G.edges_iter(data='fid'))

#make a dual graph out of the graph of the Main network based on ids (node=edge's id, edge= (edge's id, edge's id) where there is a connection between edges
Dual_G=nx.Graph()
for e in G.edges_iter(data='fid'):
    #print e[2]
    Dual_G.add_node(e[2])

for n in Dual_G.nodes():
    pass
    #print n


for i,j in G.adjacency_iter():
    #print i,j
    if len(j)==2:
        values=[]
        for k,v in j.items():
            values.append(v['fid'])
        #print values
        Dual_G.add_edge(values[0],values[1],data=None)

list(Dual_G.edges_iter())

#find connected components of the Dual graph and make sets
from networkx.algorithms.components.connected import connected_components

#lines with three connections have been included, breaks at intresections
#set also include single edges

sets=[]
for set in connected_components(Dual_G):
    sets.append(list(set))

len(sets)

#make adjacency dictionary for nodes of Dual Graph (=edges)
AdjD={}
#returns an iterator of (node, adjacency dict) tuples for all nodes
for (i, v) in Dual_G.adjacency_iter():
	#print i,v
	AdjD[i]=v


sets_in_order=[]
for set in sets:
    ord_set=[]
    nodes_passed=[]
    if len(set)==2 or len(set)==1:
        ord_set=set
        sets_in_order.append(ord_set)
    else:
        #print ord_set
        for n in set:
            #print n
            if len(AdjD[n])==1 or len(AdjD[n])>2:
                first_line=n
                #print n
            else:
                pass
        #print "broken"
        ord_set=[]
        #print ord_set
        nodes_passed.append(first_line)
        #print nodes_passed
        ord_set.append(first_line)
        #print ord_set
        for n in ord_set:
            #print n
            nodes=AdjD[n].keys()
            #print nodes
            for node in nodes:
                #print node
                if node in nodes_passed:
                    pass
                else:
                    nodes_passed.append(node)
                    ord_set.append(node)
        sets_in_order.append(ord_set)

#make a dictionary of all feature ids and corresponding geometry
D={}
for f in Main.getFeatures():
    fid=f.attribute('id')
    f_geom=f.geometryAndOwnership()
    D[fid]=f_geom

#include in sets ord the geometry of the feature
for set in sets_in_order:
    for indx,i in enumerate(set):
        ind=indx
        line=i
        set[indx]= [line,D[line]]

#combine geometries
New_geoms=[]
for set in sets_in_order:
    new_geom=None
    if len(set)==1:
        new_geom=set[0][1]
    elif len(set)==2:
        line1_geom=set[0][1]
        line2_geom=set[1][1]
        new_geom=line1_geom.combine(line2_geom)
    else:
        for i,line in enumerate(set):
            ind=i
            l=line
            if ind==(len(set)-1):
                pass
            else:
                l_geom=set[ind][1]
                next_l=set[(ind+1)%len(set)]
                next_l_geom=set[(ind+1)%len(set)][1]
                new_geom=l_geom.combine(next_l_geom)
                set[(ind+1)%len(set)][1]=new_geom
    #print new_geom
    New_geoms.append(new_geom)

#add a writer to write new features
provider=Main.dataProvider()
merged_writer = QgsVectorFileWriter ("/Users/joe/Documents/2015_Localities/Merged_Foreground.shp", "UTF-8" , provider.fields() ,provider.geometryType(), provider.crs() , "ESRI Shapefile")

if merged_writer.hasError() != QgsVectorFileWriter.NoError:
    print "Error when creating shapefile: ",  primary_writer.errorMessage()

del merged_writer
Merged_FNet=QgsVectorLayer ("/Users/joe/Documents/2015_Localities/Merged_Foreground.shp", 'Merged_FNet', 'ogr')
QgsMapLayerRegistry.instance().addMapLayer(Merged_FNet)

id=0
for i in New_geoms:
  # add a feature
  feature = QgsFeature()
  feature.setGeometry( i )
  attr = [id]
  feature.setAttributes(attr)
  Merged_FNet.startEditing()
  Merged_FNet.addFeature(feature, True)
  Merged_FNet.commitChanges()
  id+=1
















####################### Step 3: Extend background to foreground network

####################### Step 4: Merge two networks into one spatial models

####################### Step 5: Simplify network by preserving its topology
#Simplification should include:
#1. remove vertices
#2. remove small segments

####################### Step 6: Generate unlinks in intersections

####################### Step 7: Clean the model
#1. remove lines with length = 0
#2. remove invalid geometry
#3. remove isolated lines
#4. snap lines