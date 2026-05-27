import sys
from pathlib import Path

# Добавляем корневую директорию в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from fastapi import status


class TestAPI:

    # GET / - получение списка файлов
    def test_get_file_list_empty(self, test_client):
        """Тест: получение списка файлов когда нет файлов"""
        response = test_client.get("/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["files"] == []
        assert data["count"] == 0

    def test_get_file_list_with_files(self, test_client):
        """Тест: получение списка файлов когда есть файлы"""
        # Создаем файлы через API
        test_client.post("/", json={"file_name": "file1", "content": "content1"})
        test_client.post("/", json={"file_name": "file2", "content": "content2"})

        response = test_client.get("/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["files"]) == 2
        assert "file1" in data["files"]
        assert "file2" in data["files"]
        assert data["count"] == 2

    # GET /{file_name} - чтение файла
    def test_read_file_success(self, test_client):
        """Тест: успешное чтение файла"""
        # Создаем файл через API
        test_client.post("/", json={"file_name": "test", "content": "Hello World"})

        response = test_client.get("/test")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["file_name"] == "test"
        assert data["content"] == "Hello World"

    def test_read_file_not_found(self, test_client):
        """Тест: чтение несуществующего файла"""
        response = test_client.get("/not_exists")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "не найден" in response.json()["detail"]

    def test_read_file_invalid_name(self, test_client):
        """Тест: чтение файла с невалидным именем"""
        # FastAPI не может найти маршрут с "/" в пути
        response = test_client.get("/test/file")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    # POST / - создание файла
    def test_create_file_success(self, test_client, sample_file_data):
        """Тест: успешное создание файла"""
        response = test_client.post("/", json=sample_file_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["file_name"] == sample_file_data["file_name"]
        assert data["content"] == sample_file_data["content"]

    def test_create_file_empty_content(self, test_client):
        """Тест: создание файла с пустым содержимым"""
        response = test_client.post("/", json={
            "file_name": "empty_file"
        })

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["file_name"] == "empty_file"
        assert data["content"] == ""

    def test_create_file_duplicate(self, test_client):
        """Тест: создание дубликата файла"""
        import time
        unique_name = f"duplicate_test_{int(time.time())}"
        test_data = {
            "file_name": unique_name,
            "content": "test content"
        }

        # Первое создание
        response1 = test_client.post("/", json=test_data)
        assert response1.status_code == status.HTTP_201_CREATED

        # Второе создание (дубликат)
        response2 = test_client.post("/", json=test_data)
        assert response2.status_code == status.HTTP_409_CONFLICT
        assert "уже существует" in response2.json()["detail"]

    def test_create_file_empty_string_name(self, test_client):
        """Тест: создание файла с пустой строкой - ошибка Pydantic (422)"""
        response = test_client.post("/", json={
            "file_name": "",
            "content": "content"
        })

        # Пустая строка - Pydantic validation error (min_length=1)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_create_file_spaces_only_name(self, test_client):
        """Тест: создание файла с пробелами - ошибка FileManager (400)"""
        response = test_client.post("/", json={
            "file_name": "   ",
            "content": "content"
        })

        # Пробелы проходят Pydantic (не пустая строка), но FileManager возвращает 400
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "пустым" in response.json()["detail"]

    @pytest.mark.parametrize("invalid_name,expected_msg", [
        ("test/file", "содержать символ"),
        ("test\\file", "содержать символ"),
        ("test:file", "содержать символ"),
        ("test*file", "содержать символ"),
        ("test?file", "содержать символ"),
        ("test<file", "содержать символ"),
        ("test>file", "содержать символ"),
        ("test|file", "содержать символ"),
    ])
    def test_create_file_invalid_chars(self, test_client, invalid_name, expected_msg):
        """Тест: создание файла с запрещенными символами - ошибка FileManager (400)"""
        response = test_client.post("/", json={
            "file_name": invalid_name,
            "content": "content"
        })

        # FileManager validation error
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert expected_msg in response.json()["detail"]

    def test_create_file_missing_file_name(self, test_client):
        """Тест: создание файла без указания имени"""
        response = test_client.post("/", json={
            "content": "some content"
        })

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    # Интеграционные тесты
    def test_full_workflow(self, test_client):
        """Тест: полный цикл работы с файлом"""
        import time
        file_name = f"workflow_test_{int(time.time())}"
        content = "Initial content"

        # 1. Создаем файл
        create_response = test_client.post("/", json={
            "file_name": file_name,
            "content": content
        })
        assert create_response.status_code == status.HTTP_201_CREATED

        # 2. Получаем список файлов (должен быть наш файл)
        list_response = test_client.get("/")
        assert list_response.status_code == status.HTTP_200_OK
        assert file_name in list_response.json()["files"]

        # 3. Читаем файл
        read_response = test_client.get(f"/{file_name}")
        assert read_response.status_code == status.HTTP_200_OK
        assert read_response.json()["content"] == content

        # 4. Проверяем ошибку при повторном создании
        duplicate_response = test_client.post("/", json={
            "file_name": file_name,
            "content": "New content"
        })
        assert duplicate_response.status_code == status.HTTP_409_CONFLICT

    def test_concurrent_requests(self, test_client):
        """Тест: несколько запросов подряд"""
        import time
        timestamp = int(time.time())

        responses = []
        for i in range(5):
            response = test_client.post("/", json={
                "file_name": f"concurrent_test_{timestamp}_{i}",
                "content": f"Content {i}"
            })
            responses.append(response)

        # Все запросы должны быть успешными
        for response in responses:
            assert response.status_code == status.HTTP_201_CREATED

        # Проверяем, что все файлы создались
        list_response = test_client.get("/")
        files = list_response.json()["files"]
        assert len([f for f in files if f.startswith(f"concurrent_test_{timestamp}")]) == 5