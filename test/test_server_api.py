import pytest
import sys
import os
import io

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'web', 'backend')))

# We need to mock models before importing server to avoid heavy GPU initialization
@pytest.fixture
def mock_server(mocker):
    # Mock initialize_models in server.py
    mocker.patch('server.initialize_models', return_value=None)
    
    import server
    # Fake global state for pipelines
    server.pipe = mocker.MagicMock()
    server.pipe_stage1 = mocker.MagicMock()
    server.pipe_stage2 = mocker.MagicMock()
    server.device = 'cpu'
    
    class FakeConfig:
        width = 400
        height = 600
        output_format = 'png'
        checkpoint_name = 'test'
        output_dir = './output_test'
        
    server.server_config = FakeConfig()
    
    server.app.config['TESTING'] = True
    return server.app.test_client()

def test_status_endpoint(mock_server):
    response = mock_server.get('/status')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'ready'
    assert 'basic_mode' in data

def test_preview_missing_image(mock_server):
    response = mock_server.post('/preview')
    # Should return 400 for missing image
    assert response.status_code == 400
    data = response.get_json()
    assert 'No image file provided' in data['error']

def test_preview_invalid_params(mock_server):
    # Create a fake image payload with invalid parameters
    data = {
        'image': (io.BytesIO(b"fake image data"), 'test.jpg'),
        'params': '{"width": -100}' # Invalid width, should be positive
    }
    response = mock_server.post('/preview', data=data, content_type='multipart/form-data')
    assert response.status_code == 400
    data_json = response.get_json()
    assert 'error' in data_json
