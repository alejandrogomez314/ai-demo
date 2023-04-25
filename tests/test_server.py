import io
from flask import Flask
from flask_testing import TestCase
from app import predict_route

class FlaskAppTestCase(TestCase):
    def create_app(self):
        # Create and configure the Flask app instance for testing
        app = Flask(__name__)
        app.config.from_object('app.TestConfig')
        return app

    def test_predict_route_success(self):
        # Test successful prediction route
        file_data = "This is a test file data."
        file = (io.BytesIO(file_data.encode()), 'test.txt')
        response = self.client.post('/predict', data={'file': file})
        self.assert200(response)
        self.assertJSONKeyEqual(response.json, 'result', 'Prediction result')

    def test_predict_route_no_file(self):
        # Test prediction route with no file
        response = self.client.post('/predict')
        self.assert400(response)
        self.assertJSONKeyEqual(response.json, 'error', 'No file found in the request.')

    def test_predict_route_empty_filename(self):
        # Test prediction route with empty filename
        file = (io.BytesIO(b''), '')
        response = self.client.post('/predict', data={'file': file})
        self.assert400(response)
        self.assertJSONKeyEqual(response.json, 'error', 'File name is empty.')

    def test_predict_route_invalid_extension(self):
        # Test prediction route with invalid file extension
        file = (io.BytesIO(b'This is a test file data.'), 'test.png')
        response = self.client.post('/predict', data={'file': file})
        self.assert400(response)
        self.assertJSONKeyEqual(response.json, 'error', 'File has an invalid extension. Allowed extensions are txt and csv.')

    def test_predict_route_prediction_error(self):
    # Test prediction route with prediction error
        file_data = "This is a test file data."
        file = (io.BytesIO(file_data.encode()), 'test.txt')
        # Mock predict function to raise an error
        def mock_predict(data):
            raise Exception('Failed to predict')
        self.app.predict = mock_predict
        response = self.client.post('/predict', data={'file': file})
        self.assertStatus(response, 500)
        self.assertIn('error', response.json)