import pytest

from filemanager import FileManager


class TestFileManager:
    def test_init_creates_directory(self, temp_dir):
        FileManager(base_path=temp_dir)

        assert temp_dir.exists()
        assert temp_dir.is_dir()

    def test_create_file_success(self, file_manager):
        result = file_manager.create_file("test", "content")

        assert result == {"file_name": "test", "content": "content"}
        assert file_manager._get_file_path("test").read_text(encoding="utf-8") == "content"

    def test_create_file_empty_content(self, file_manager):
        result = file_manager.create_file("empty_file")

        assert result == {"file_name": "empty_file", "content": ""}
        assert file_manager._get_file_path("empty_file").read_text(encoding="utf-8") == ""

    def test_create_file_duplicate(self, file_manager):
        file_manager.create_file("test", "content")

        with pytest.raises(FileExistsError, match="already exists"):
            file_manager.create_file("test", "new content")

    def test_create_file_invalid_name(self, file_manager):
        invalid_names = ["", "   ", "test/file", "test\\file", "test:file"]

        for name in invalid_names:
            with pytest.raises(ValueError):
                file_manager.create_file(name, "content")

    def test_get_file_success(self, file_manager):
        file_manager.create_file("test", "Hello World")

        result = file_manager.get_file("test")

        assert result == {"file_name": "test", "content": "Hello World"}

    def test_get_file_not_found(self, file_manager):
        with pytest.raises(FileNotFoundError, match="not found"):
            file_manager.get_file("not_exists")

    def test_get_file_invalid_name(self, file_manager):
        with pytest.raises(ValueError, match="reserved characters"):
            file_manager.get_file("test/file")

    def test_get_all_files_empty(self, file_manager):
        assert file_manager.get_all_files() == []

    def test_get_all_files_with_files(self, file_manager):
        file_manager.create_file("file1", "content1")
        file_manager.create_file("file2", "content2")
        file_manager.create_file("file3", "content3")

        assert file_manager.get_all_files() == ["file1", "file2", "file3"]

    def test_validate_file_name(self, file_manager):
        valid_names = ["valid", "valid_name", "valid-name", "valid.name", "valid123"]
        for name in valid_names:
            assert file_manager._validate_file_name(name) == name

        invalid_names = ["", "   ", "test/file", "test\\file", "test:file"]
        for name in invalid_names:
            with pytest.raises(ValueError):
                file_manager._validate_file_name(name)

    def test_get_file_path(self, file_manager):
        path = file_manager._get_file_path("test")

        assert path.name == "test.txt"
        assert path.parent == file_manager.base_path
