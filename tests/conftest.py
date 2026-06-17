import shutil
import sys
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))

import filemanager as filemanager_module
from filemanager import FileManager
from main import main_app


@pytest.fixture
def temp_dir():
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def file_manager(temp_dir):
    return FileManager(base_path=temp_dir)


@pytest.fixture
def test_client(file_manager):
    original_manager = filemanager_module.file_manager
    filemanager_module.file_manager = file_manager

    with TestClient(main_app) as client:
        yield client

    filemanager_module.file_manager = original_manager


@pytest.fixture
def sample_file_data():
    return {
        "file_name": "test_file",
        "content": "Hello, World!",
    }
