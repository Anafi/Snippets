# a script to join two networks into one
# by using nodes bridges
# is it needed to have a node bridge for every connection?

# main network
n_main = iface.mapCanvas().currentLayer()

# sub-network
n_sub = iface.mapCanvas().currentLayer()

# fix projections
# exp_crs = QgsCoordinateReferenceSystem(4326, QgsCoordinateReferenceSystem.EpsgCrsId)
# self.layer.setCoordinateSystem(XXX) where XXX is defined like above using:
# QgsCoordinateReferenceSystem(4326, QgsCoordinateReferenceSystem.EpsgCrsId)

# store initial connectivity values (only for ITN)

# read and combine attributes (e.g. class OS and type OSM)
