from pathlib import Path
from typing import Optional


class FileManager:
    """Manage text files inside a single base directory."""

    INVALID_NAME_CHARS = set('/\\:*?"<>|')

    def __init__(self, base_path: Optional[Path] = None):
        if base_path is None:
            base_path = Path(__file__).parent / "files"

        self.base_path = base_path
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

    def _get_file_path(self, file_name: str) -> Path:
        safe_name = self._validate_file_name(file_name)
        file_path = self.base_path / f"{safe_name}.txt"

        base_path = self.base_path.resolve()
        resolved_path = file_path.resolve()
        if base_path not in resolved_path.parents and resolved_path != base_path:
            raise ValueError("File path escapes the files directory")

        return file_path

    def get_all_files(self) -> list[str]:
        files = [
            file.stem
            for file in self.base_path.iterdir()
            if file.is_file() and file.suffix == ".txt"
        ]
        return sorted(files)

    def get_file(self, file_name: str) -> dict[str, str]:
        safe_name = self._validate_file_name(file_name)
        file_path = self._get_file_path(safe_name)

        if not file_path.exists():
            raise FileNotFoundError(f"File '{safe_name}' not found")

        content = file_path.read_text(encoding="utf-8")
        return {
            "file_name": safe_name,
            "content": content,
        }

    def create_file(self, file_name: str, content: str = "") -> dict[str, str]:
        safe_name = self._validate_file_name(file_name)
        file_path = self._get_file_path(safe_name)

        if file_path.exists():
            raise FileExistsError(f"File '{safe_name}' already exists")

        file_path.write_text(content, encoding="utf-8")
        return {
            "file_name": safe_name,
            "content": content,
        }


file_manager = FileManager()
