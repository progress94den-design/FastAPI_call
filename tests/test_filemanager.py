import sys
from pathlib import Path

# Добавляем корневую директорию в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from filemanager import FileManager


class TestFileManager:

    def test_init_creates_directory(self, temp_dir):
        """Тест: инициализация создает директорию"""
        manager = FileManager(base_path=temp_dir)
        assert temp_dir.exists()
        assert temp_dir.is_dir()

    def test_create_file_success(self, file_manager):
        """Тест: успешное создание файла"""
        result = file_manager.create_file("test", "content")

        assert result["file_name"] == "test"
        assert result["content"] == "content"

        # Проверяем, что файл действительно создался
        file_path = file_manager._get_file_path("test")
        assert file_path.exists()

        with open(file_path, "r", encoding="utf-8") as f:
            assert f.read() == "content"

    def test_create_file_empty_content(self, file_manager):
        """Тест: создание файла с пустым содержимым"""
        result = file_manager.create_file("empty_file")

        assert result["file_name"] == "empty_file"
        assert result["content"] == ""

        file_path = file_manager._get_file_path("empty_file")
        assert file_path.exists()
        assert file_path.stat().st_size == 0

    def test_create_file_duplicate(self, file_manager):
        """Тест: попытка создать существующий файл"""
        file_manager.create_file("test", "content")

        with pytest.raises(FileExistsError) as exc:
            file_manager.create_file("test", "new content")

        assert "уже существует" in str(exc.value)


    def test_create_file_invalid_name(self, file_manager):
        """Тест: создание файла с невалидным именем"""
        invalid_names = ["", "   ", "test/file", "test\\file", "test:file"]

        for name in invalid_names:
            with pytest.raises(ValueError) as exc:
                file_manager.create_file(name, "content")
            assert "не может" in str(exc.value) or "пустым" in str(exc.value)

    def test_get_file_success(self, file_manager):
        """Тест: успешное чтение файла"""
        # Сначала создаем файл
        file_manager.create_file("test", "Hello World")

        # Читаем файл
        result = file_manager.get_file("test")

        assert result["file_name"] == "test"
        assert result["content"] == "Hello World"

    def test_get_file_not_found(self, file_manager):
        """Тест: чтение несуществующего файла"""
        with pytest.raises(FileNotFoundError) as exc:
            file_manager.get_file("not_exists")

        assert "не найден" in str(exc.value)

    def test_get_file_invalid_name(self, file_manager):
        """Тест: чтение файла с невалидным именем"""
        with pytest.raises(ValueError) as exc:
            file_manager.get_file("test/file")

        assert "не может содержать символ" in str(exc.value)

    def test_get_all_files_empty(self, file_manager):
        """Тест: получение списка файлов из пустой директории"""
        files = file_manager.get_all_files()
        assert files == []

    def test_get_all_files_with_files(self, file_manager):
        """Тест: получение списка файлов"""
        # Создаем несколько файлов
        file_manager.create_file("file1", "content1")
        file_manager.create_file("file2", "content2")
        file_manager.create_file("file3", "content3")

        files = file_manager.get_all_files()

        assert len(files) == 3
        assert "file1" in files
        assert "file2" in files
        assert "file3" in files
        assert files == sorted(files)  # Проверяем сортировку

    def test_validate_file_name(self, file_manager):
        """Тест: валидация имени файла"""
        # Валидные имена
        valid_names = ["valid", "valid_name", "valid-name", "valid.name", "valid123"]
        for name in valid_names:
            assert file_manager._validate_file_name(name) == name

        # Невалидные имена
        invalid_names = ["", "   ", "test/file", "test\\file", "test:file"]
        for name in invalid_names:
            with pytest.raises(ValueError):
                file_manager._validate_file_name(name)

    def test_get_file_path(self, file_manager):
        """Тест: получение пути к файлу"""
        path = file_manager._get_file_path("test")
        assert str(path).endswith("test.txt")
        assert path.parent == file_manager.base_path