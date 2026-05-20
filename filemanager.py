import shutil
import uuid
from pathlib import Path
from typing import Optional


class FileManager:
    """
    Класс для управления файлами в директории /files
    """

    def __init__(self, base_path: Optional[Path] = None):
        """
        Инициализация менеджера файлов

        Args:
            base_path: путь к директории с файлами (по умолчанию: ./files)
        """
        if base_path is None:
            base_path = Path(__file__).parent / "files"

        self.base_path = base_path
        self._ensure_directory_exists()

    def _ensure_directory_exists(self) -> None:
        """Создает директорию для файлов, если она не существует"""
        self.base_path.mkdir(exist_ok=True)

    def _get_file_path(self, file_name: str) -> Path:
        """
        Получает полный путь к файлу
        Args:
            file_name: имя файла без расширения
        Returns:
            Path: полный путь к файлу
        """
        return self.base_path / f"{file_name}.txt"

    def get_all_files(self) -> list[str]:
        """
        Получает список всех файлов (без расширения)
        Returns:
            List[str]: список имен файлов
        """
        files = [
            file.stem for file in self.base_path.iterdir()
            if file.is_file() and file.suffix == '.txt'
        ]
        return sorted(files)

    def get_file(self, file_name: str) -> dict:
        """
        Получает содержимое файла (1 строчка)
        Args:
            file_name: имя файла без расширения
        Returns:
            dict: словарь с именем файла и содержимым
        Raises:
            FileNotFoundError: если файл не найден
            ValueError: если имя файла некорректно
        """
        file_path = self._get_file_path(file_name)

        if not file_path.exists():
            raise FileNotFoundError(f"Файл '{file_name}' не найден")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.readline()

            return {
                "file_name": file_name,
                "content": content
            }
        except Exception as e:
            raise Exception(f"Ошибка при чтении файла: {str(e)}")

    def post_file(self, file) -> dict:
        """
        Загружает содержимое файла, генерируя имя через UUID.
        Args:
            file: UploadFile объект
        Returns:
            dict: словарь с именем файла и содержимым
        Raises:
            ValueError: если имя файла некорректно
            Exception: при ошибках записи
        """
        file_name = str(uuid.uuid4())
        file_path = self._get_file_path(file_name)

        try:
            with file_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            raise Exception(f"Ошибка при сохранении файла: {str(e)}")

        return self.get_file(file_name)

# Создаем экземпляр менеджера файлов
file_manager = FileManager()
