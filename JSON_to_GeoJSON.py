
# connect to TfL's URL and request all data you need


# (copied) convert JSON file to GEOJSON

def convert_json(items):
    import json
    return json.dumps(dict(type="FeatureCollection", features=[
        {"type": "Feature",
         "geometry": {"type": "Point",
                      "coordinates": [feature['lon'],
                                      feature['lat']]},
         "properties": {key: value
                        for key, value in feature.items()
                        if key not in ('lat', 'lon')}
         }
        for feature in json.loads(items)
        ]))