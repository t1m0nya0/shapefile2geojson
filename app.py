import os
import json
import uuid
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from zipfile import ZipFile
import geopandas as gpd
import shutil

ALLOWED_EXTENSIONS = set(['zip'])
UPLOAD_FOLDER = 'uploads'
TMP_FOLDER = 'tmp/'

app = Flask(__name__)
app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def remove_contents_of_folders(folders):
    """
    Удаляет содержимое указанных папок рекурсивно.

    Аргументы:
    folders (list): Список путей к папкам, содержимое которых нужно удалить.

    Возвращает:
    None
    """
    for folder in folders:
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')


def find_shp_file(root_folder):
    for root, dirs, files in os.walk(root_folder):
        for file in files:
            if file.endswith('.shp'):
                return os.path.join(root, file)
    return None


@app.route('/convert', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        uploadfilename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())
        temp_folder = os.path.join(TMP_FOLDER, unique_id)
        os.makedirs(temp_folder)

        file.save(os.path.join(app.config['UPLOAD_FOLDER'], uploadfilename))

        # Extract the uploaded ZIP file
        zip_path = os.path.join(app.config['UPLOAD_FOLDER'], uploadfilename)
        if not os.path.exists(zip_path):
            return jsonify({'error': 'Uploaded file not found on server'}), 400

        with ZipFile(zip_path, 'r') as zipfile:
            # Extract all files, including hidden ones (like __MACOSX)
            for member in zipfile.infolist():
                zipfile.extract(member, path=temp_folder)

        # Find the .shp file in the extracted folder structure
        shp_file = find_shp_file(temp_folder)
        if shp_file is None:
            return jsonify({'error': 'Shapefile (.shp) not found in the ZIP archive'}), 400

        # Read the shapefile and convert to GeoJSON
        gdf = gpd.read_file(shp_file)
        geojson_file = os.path.join('geofiles', f'{unique_id}.json')
        gdf.to_file(geojson_file, driver='GeoJSON')

        # Clean up extracted files
        for root, dirs, files in os.walk(temp_folder, topdown=False):
            for file in files:
                os.unlink(os.path.join(root, file))
            for dir in dirs:
                os.rmdir(os.path.join(root, dir))
        os.rmdir(temp_folder)

        # Delete the uploaded ZIP file
        os.unlink(zip_path)

        # Read GeoJSON file and return it
        with open(geojson_file) as json_file:
            data = json.load(json_file)

        resp = jsonify({'message': 'File uploaded! GeoJSON created!', 'geojson': data})
        resp.status_code = 201

        # Clean up folders geofiles, tmp, uploads
        folders_to_clean = ['geofiles', 'tmp', 'uploads']
        remove_contents_of_folders(folders_to_clean)

        return resp

    else:
        return jsonify({'error': 'Invalid file format. Allowed format is ZIP'}), 400


if __name__ == "__main__":
    app.run(debug=True)
