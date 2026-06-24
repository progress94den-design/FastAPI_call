from pathlib import Path
from typing import Optional, Protocol


class FileReaderStrategy(Protocol):
    """Read a file and extract text from it."""

    def read(self, file_path: Path) -> str:
        ...


class TextFileReader:
    def read(self, file_path: Path) -> str:
        return file_path.read_text(encoding="utf-8")


class PdfFileReader:
    def read(self, file_path: Path) -> str:
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise ValueError("PDF support requires the 'pypdf' package") from exc

        reader = PdfReader(file_path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)


class DocxFileReader:
    def read(self, file_path: Path) -> str:
        try:
            from docx import Document
        except ImportError as exc:
            raise ValueError("DOCX support requires the 'python-docx' package") from exc

        document = Document(file_path)
        return "\n".join(paragraph.text for paragraph in document.paragraphs)


class FileManager:
    """Manage supported files inside a single base directory."""

    INVALID_NAME_CHARS = set('/\\:*?"<>|')
    DEFAULT_READERS: dict[str, FileReaderStrategy] = {
        ".txt": TextFileReader(),
        ".md": TextFileReader(),
        ".pdf": PdfFileReader(),
        ".docx": DocxFileReader(),
    }

    def __init__(
        self,
        base_path: Optional[Path] = None,
        readers: Optional[dict[str, FileReaderStrategy]] = None,
    ):
        if base_path is None:
            base_path = Path(__file__).parent / "files"

        self.base_path = base_path
        self.readers = readers or self.DEFAULT_READERS
        self._ensure_directory_exists()

    def _ensure_directory_exists(self) -> None:
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _validate_file_name(self, file_name: str) -> str:
        if not isinstance(file_name, str):
            raise ValueError("File name must be a string")

        normalized_name = file_name.strip()
        if not normalized_name:
            raise ValueError("File name cannot be empty")

        if normalized_name in {".", ".."}:
            raise ValueError("File name cannot be a reserved path segment")

        if any(char in normalized_name for char in self.INVALID_NAME_CHARS):
            raise ValueError("File name cannot contain path or reserved characters")

        return normalized_name

    def _validate_extension(self, extension: str) -> str:
        normalized_extension = extension.lower()
        if normalized_extension not in self.readers:
            raise ValueError(f"Unsupported file format: {extension}")

        return normalized_extension

    def _validate_base_path(self, file_path: Path) -> Path:
        base_path = self.base_path.resolve()
        resolved_path = file_path.resolve(strict=False)
        if base_path not in resolved_path.parents and resolved_path != base_path:
            raise ValueError("File path escapes the files directory")

        return file_path

    def _split_uploaded_file_name(self, file_name: str) -> tuple[str, str]:
        safe_file_name = self._validate_file_name(file_name)
        file_path = Path(safe_file_name)
        stem = self._validate_file_name(file_path.stem)
        extension = self._validate_extension(file_path.suffix)
        return stem, extension

    def _get_file_path(self, file_name: str, extension: str) -> Path:
        safe_name = self._validate_file_name(file_name)
        safe_extension = self._validate_extension(extension)
        return self._validate_base_path(self.base_path / f"{safe_name}{safe_extension}")

    def resolve_file(self, file_name: str) -> Path:
        safe_name = self._validate_file_name(file_name)
        matches = [
            file
            for file in self.base_path.iterdir()
            if file.is_file()
            and file.stem == safe_name
            and file.suffix.lower() in self.readers
        ]

        if not matches:
            raise FileNotFoundError(f"File '{safe_name}' not found")

        if len(matches) > 1:
            raise ValueError(f"File '{safe_name}' has multiple supported formats")

        return self._validate_base_path(matches[0])

    def get_all_files(self) -> list[str]:
        files = [
            file.stem
            for file in self.base_path.iterdir()
            if file.is_file() and file.suffix.lower() in self.readers
        ]
        return sorted(set(files))

    def get_file(self, file_name: str) -> dict[str, str]:
        safe_name = self._validate_file_name(file_name)
        file_path = self.resolve_file(safe_name)
        reader = self.readers[file_path.suffix.lower()]

        content = reader.read(file_path)
        return {
            "file_name": safe_name,
            "content": content,
        }

    def upload_file(self, file_name: str, content: bytes) -> dict[str, str]:
        safe_name, extension = self._split_uploaded_file_name(file_name)
        file_path = self._get_file_path(safe_name, extension)

        try:
            self.resolve_file(safe_name)
        except FileNotFoundError:
            pass
        else:
            raise FileExistsError(f"File '{safe_name}' already exists")

        file_path.write_bytes(content)
        return self.get_file(safe_name)


file_manager = FileManager()
