from flask import Flask, request, jsonify
from functools import reduce
from pypdf import PdfReader
import docx
import io

import predict_engine as engine

app = Flask(__name__)
class TestConfig:
    DEBUG = True
    TESTING = True
    # Add any other testing configurations here
    # ...
app.config.from_object('app.TestConfig')

if __name__ == '__main__':
    app.run(debug=True)  # Run the Flask app in debug mode

def convert_to_text(file, file_ext):
    if file_ext == 'txt':
        text = file.read().decode('utf-8', 'replace')
    elif file_ext == 'pdf':
        pdf_reader = PdfReader(file)
        pages = [pdf_reader.pages[i].extract_text() for i in range(len(pdf_reader.pages))]
        text = reduce(lambda x, y: x + y, pages).replace(" ", "").replace("\n", " ")
    elif file_ext in {'docx', 'pages'}:
        doc = docx.Document(io.BytesIO(file.read()))
        paragraphs = [para.text for para in doc.paragraphs]
        text = reduce(lambda x, y: x + y, paragraphs)
    else:
        raise Exception('Unsupported file extension.')
    return text

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route('/predict', methods=['POST'])
def predict_route():
    # Check if file is present in the request
    if 'file' not in request.files:
        return jsonify({'error': 'No file found in the request.'}), 400

    file = request.files['file']

    # Check if the file has a valid filename
    if file.filename == '':
        return jsonify({'error': 'File name is empty.'}), 400

    # Check if the file has an allowed extension
    allowed_extensions = {'txt', 'pdf', 'docx', 'pages'}  # Set the allowed file extensions
    file_ext = file.filename.rsplit('.', 1)[1].lower()
    if '.' not in file.filename or file_ext not in allowed_extensions:
        return jsonify({'error': 'File has an invalid extension. Allowed extensions are txt, pdf, docx, and pages.'}), 400

    # Convert file to a string
    try:
        file_data = convert_to_text(file, file_ext)
    except Exception as e:
        return jsonify({'error': f'Failed to convert file: {str(e)}'}), 500

    # Call the predict function with file_data
    try:
        results = engine.predict(file_data)  # Call the predict function with file_data
        matched_results = engine.match_skills(results)
        return jsonify({'result': matched_results}), 200
    except Exception as e:
        return jsonify({'error': f'Failed to predict: {str(e)}'}), 500