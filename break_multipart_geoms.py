def break_multiparts(shp):
    feat_to_del = []
    New_feat = []
    for f in shp.getFeatures():
        f_geom_type = f.geometry().wkbType()
        if f_geom_type == 5:
            f_id = f.id()
            attr = f.attributes()
            new_geoms = f.geometry().asGeometryCollection()
            for i in new_geoms:
                new_feat = QgsFeature()
                new_feat.setGeometry(i)
                new_feat.setAttributes(attr)
                New_feat.append(new_feat)
            feat_to_del.append(f_id)

    shp.startEditing()
    shp.addFeatures(New_feat)
    shp.removeSelection()
    shp.select(feat_to_del)
    shp.deleteSelectedFeatures()
    shp.commitChanges()
    shp.removeSelection()