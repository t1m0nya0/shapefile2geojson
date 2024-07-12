import os
import urllib.request
import json
from flask import Flask, request, redirect, jsonify
from werkzeug.utils import secure_filename
from zipfile import ZipFile
import geopandas as gpd

ALLOWED_EXTENSIONS = set(['zip'])
UPLOAD_FOLDER = 'uploads'
TMP_FOLDER = 'tmp/'

app = Flask(__name__)
app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
  return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/convert', methods=['POST'])
def upload_file():
  file = request.files['file']
  uploadfilename = secure_filename(file.filename)
  # salva o arquivo recebido
  file.save(os.path.join(app.config['UPLOAD_FOLDER'], uploadfilename))

  # descompacta
  zipfile = ZipFile(os.path.join('zip://', os.getcwd(), app.config['UPLOAD_FOLDER'], uploadfilename))
  zipfile.extractall(path=TMP_FOLDER)

  # pega os arquivos com as extensoes esperadas
  filenames = [y for y in sorted(zipfile.namelist()) for ending in ['dbf', 'prj', 'shp', 'shx'] if y.endswith(ending)]
  dbf, prj, shp, shx = [filename for filename in filenames]

  # le o shapefile e converte em geoJson
  usa = gpd.read_file(TMP_FOLDER + shp)
  usa.to_file("./geofiles/shape.json", driver='GeoJSON')

  # exclui os arquivos descompactados
  for filename in filenames:
    os.unlink(os.path.join(TMP_FOLDER, filename))
  # exclui o arquivo enviado
  os.unlink(os.path.join(app.config['UPLOAD_FOLDER'], uploadfilename))

  with open("./geofiles/shape.json") as json_file:
    data = json.load(json_file)

  resp = jsonify({'message' : 'File uploaded! GeoJson created!', 'geojson': data})
  resp.status_code = 201
  return resp

if __name__ == "__main__":
  app.run()