import sys
from pathlib import Path

# Добавляем корневую директорию в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import tempfile
import shutil
from fastapi.testclient import TestClient

from main import main_app
from filemanager import FileManager


@pytest.fixture(scope="function")
def temp_dir():
    """Создает временную директорию для тестов"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    # Удаляем после тестов
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture(scope="function")
def file_manager(temp_dir):
    """Создает FileManager с временной директорией"""
    return FileManager(base_path=temp_dir)


@pytest.fixture(scope="function")
def test_client(file_manager):
    """Создает тестовый клиент FastAPI с подмененным file_manager"""
    import filemanager as fm_module

    # Сохраняем оригинальный менеджер
    original_manager = fm_module.file_manager

    # Подменяем на тестовый (который использует временную директорию)
    fm_module.file_manager = file_manager

    # Создаем тестовый клиент
    with TestClient(main_app) as client:
        yield client

    # Восстанавливаем оригинальный менеджер
    fm_module.file_manager = original_manager


@pytest.fixture
def sample_file_data():
    """Пример данных для создания файла"""
    return {
        "file_name": "test_file",
        "content": "Hello, World!"
    }