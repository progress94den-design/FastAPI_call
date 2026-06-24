from pathlib import Path

import pytest

from filemanager import DocxFileReader, FileManager, PdfFileReader


class StubReader:
    def __init__(self, content: str):
        self.content = content
        self.read_paths: list[Path] = []

    def read(self, file_path: Path) -> str:
        self.read_paths.append(file_path)
        return self.content


class TestFileManager:
    def test_init_creates_directory(self, temp_dir):
        FileManager(base_path=temp_dir)

        assert temp_dir.exists()
        assert temp_dir.is_dir()

    def test_upload_file_success(self, file_manager):
        result = file_manager.upload_file("test.txt", b"content")

        assert result == {"file_name": "test", "content": "content"}
        assert (file_manager.base_path / "test.txt").read_bytes() == b"content"

    def test_upload_file_keeps_original_extension(self, file_manager):
        file_manager.upload_file("notes.md", b"# Title")

        assert (file_manager.base_path / "notes.md").exists()

    def test_upload_file_duplicate_stem(self, file_manager):
        file_manager.upload_file("report.txt", b"content")

        with pytest.raises(FileExistsError, match="already exists"):
            file_manager.upload_file("report.md", b"new content")

    def test_upload_file_invalid_name(self, file_manager):
        invalid_names = ["", "   ", "test/file.txt", "test\\file.txt", "test:file.txt"]

        for name in invalid_names:
            with pytest.raises(ValueError):
                file_manager.upload_file(name, b"content")

    def test_upload_file_unsupported_format(self, file_manager):
        with pytest.raises(ValueError, match="Unsupported file format"):
            file_manager.upload_file("image.png", b"content")

    def test_get_file_success(self, file_manager):
        file_manager.upload_file("test.txt", b"Hello World")

        result = file_manager.get_file("test")

        assert result == {"file_name": "test", "content": "Hello World"}

    def test_get_markdown_file_success(self, file_manager):
        file_manager.upload_file("readme.md", b"# Hello")

        result = file_manager.get_file("readme")

        assert result == {"file_name": "readme", "content": "# Hello"}

    def test_get_file_uses_strategy_for_extension(self, temp_dir):
        pdf_reader = StubReader("pdf text")
        file_manager = FileManager(base_path=temp_dir, readers={".pdf": pdf_reader})
        (temp_dir / "report.pdf").write_bytes(b"%PDF")

        result = file_manager.get_file("report")

        assert result == {"file_name": "report", "content": "pdf text"}
        assert pdf_reader.read_paths == [temp_dir / "report.pdf"]

    def test_pdf_reader_returns_string(self, temp_dir):
        from pypdf import PdfWriter

        pdf_path = temp_dir / "blank.pdf"
        writer = PdfWriter()
        writer.add_blank_page(width=72, height=72)
        with pdf_path.open("wb") as file:
            writer.write(file)

        assert PdfFileReader().read(pdf_path) == ""

    def test_docx_reader_returns_text(self, temp_dir):
        from docx import Document

        docx_path = temp_dir / "document.docx"
        document = Document()
        document.add_paragraph("Hello DOCX")
        document.save(docx_path)

        assert DocxFileReader().read(docx_path) == "Hello DOCX"

    def test_get_file_not_found(self, file_manager):
        with pytest.raises(FileNotFoundError, match="not found"):
            file_manager.get_file("not_exists")

    def test_get_file_invalid_name(self, file_manager):
        with pytest.raises(ValueError, match="reserved characters"):
            file_manager.get_file("test/file")

    def test_get_all_files_empty(self, file_manager):
        assert file_manager.get_all_files() == []

    def test_get_all_files_with_supported_files(self, file_manager):
        file_manager.upload_file("file1.txt", b"content1")
        file_manager.upload_file("file2.md", b"content2")
        (file_manager.base_path / "image.png").write_bytes(b"ignored")

        assert file_manager.get_all_files() == ["file1", "file2"]

    def test_validate_file_name(self, file_manager):
        valid_names = ["valid", "valid_name", "valid-name", "valid.name", "valid123"]
        for name in valid_names:
            assert file_manager._validate_file_name(name) == name

        invalid_names = ["", "   ", "test/file", "test\\file", "test:file"]
        for name in invalid_names:
            with pytest.raises(ValueError):
                file_manager._validate_file_name(name)

    def test_get_file_path(self, file_manager):
        path = file_manager._get_file_path("test", ".txt")

        assert path.name == "test.txt"
        assert path.parent == file_manager.base_path

    def test_resolve_file(self, file_manager):
        file_manager.upload_file("test.md", b"content")

        assert file_manager.resolve_file("test") == file_manager.base_path / "test.md"
