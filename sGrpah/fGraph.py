
# imports
import plFunctions as pF


class fGraph:

    def __init__(self, features):
        self.features = features

    # ---- ANALYSIS OPERATIONS -----

    # get fields from a feature list

    def get_fields(self):
        return self.features[0].fields()

    # dictionary of feature_id: geometry key, values

    def make_geom_dict(self,id_column):
        if id_column == 'feature_id':
            return {i.id(): i.geometryAndOwnership() for i in self.features}
        else:
            return {i[id_column]: i.geometryAndOwnership() for i in self.features}

    # dictionary of feature_id: feature_attribute key, values

    def make_attr_dict(self,id_column):
        if id_column == 'feature_id':
            return {i.id(): i.attributes() for i in self.features}
        else:
            return {i[id_column]: i.attributes() for i in self.features}

    # dictionary of feature_id: feature key, values

    def make_feat_dict(self,id_column):
        if id_column == 'feature_id':
            return {i.id(): i for i in self.features}
        else:
            return {i[id_column]: i for i in self.features}

    # dictionary of feature_id: attr_column key,values

    def fid_to_uid(self, id_column):
        return {i.id(): i[id_column] for i in self.features}

    # dictionary of feature_id: centroid
    # TODO: some of the centroids are not correct
    def make_centroids_dict(self, id_column):
        if id_column == 'feature_id':
            centroids = {i.id(): pF.pl_midpoint(i.geometry()) for i in self.features}
        else:
            uid = self.features.fid_to_uid(id_column)
            centroids = {uid[i.id()]: pF.pl_midpoint(i.geometry()) for i in self.features}
        return centroids

    # iterator of line and intersecting lines based on spatial index

    def inter_lines_iter(self):
        spIndex = QgsSpatialIndex()  # create spatial index object
        # insert features to index
        for f in self.features:
            spIndex.insertFeature(f)
        # find lines intersecting other lines
        for i in self.features:
            inter_lines = spIndex.intersects(
                QgsRectangle(QgsPoint(i.geometry().asPolyline()[0]), QgsPoint(i.geometry().asPolyline()[-1])))
            yield i.id(), inter_lines

    # ----- ALTERATION OPERATIONS -----

    # add attributes to features

    def update_uid(self, column_name, prfx):
        fid = 0
        for feat in self.features:
            feat.setAttributes(feat.attributes() + [prfx + '_' + fid])
            fid += 1

    # remove features from list

    def rmv_features(self, ids):
        pass

    # add features to list

    def add_features(self, feat_to_add):
        pass


    # find where features cross and intersect

    def find_breakages(self, id_column):
        uid = self.features.fid_to_uid(id_column)
        geometries = self.features.make_geom_dict('feature_id')
        for feat, inter_lines in self.inter_lines_iter():
            f_geom = geometries[feat]
            breakages = []
            for line in inter_lines:
                intersection = f_geom.intersection(geometries[line])
                if intersection.wkbType() == 1 and pF.point_is_vertex(intersection, f_geom):
                    breakages.append(intersection)
                # TODO: test multipoints
                elif intersection.wkbType() == 4:
                    for point in intersection.asGeometryCollection():
                        if pF.point_is_vertex(intersection, f_geom):
                            breakages.append(point)
            if len(breakages) > 0:
                yield uid[feat], set([vertex for vertex in pF.find_vertex_index(breakages, feat, geometries)])
