# Shapefile to GeoJson

REST Api to convert `shapefile` into `geojson`

* Flask
* Geopanda

Request:
``` 
POST http://localhost:5000/convert
Content-Type: multipart/form-data;

Content-Disposition: form-data; name="file"; filename="shapefile.zip"
```

Response:
```json
{
  "geojson": {
    "crs": {
      "properties": {
        "name": "urn:ogc:def:crs:OGC:1.3:CRS84"
      },
      "type": "name"
    },
    "features": [...],
    "type": "FeatureCollection"
  },
  "message": "File uploaded! GeoJson created!"
}
```