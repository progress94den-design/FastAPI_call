from fastapi import status


def upload(client, file_name: str, content: bytes | str = b"content"):
    if isinstance(content, str):
        content = content.encode("utf-8")

    return client.post(
        "/",
        files={"file": (file_name, content, "application/octet-stream")},
    )


class TestAPI:
    def test_get_file_list_empty(self, test_client):
        response = test_client.get("/")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"files": [], "count": 0}

    def test_get_file_list_with_files(self, test_client):
        upload(test_client, "file1.txt", "content1")
        upload(test_client, "file2.md", "content2")

        response = test_client.get("/")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"files": ["file1", "file2"], "count": 2}

    def test_read_file_success(self, test_client):
        upload(test_client, "test.txt", "Hello World")

        response = test_client.get("/test")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "file_name": "test",
            "content": "Hello World",
        }

    def test_read_file_not_found(self, test_client):
        response = test_client.get("/not_exists")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "File 'not_exists' not found"

    def test_read_file_invalid_path_segment(self, test_client):
        response = test_client.get("/test/file")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_upload_file_success(self, test_client):
        response = upload(test_client, "test_file.txt", "Hello, World!")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json() == {
            "file_name": "test_file",
            "content": "Hello, World!",
        }

    def test_upload_markdown_file_success(self, test_client):
        response = upload(test_client, "readme.md", "# Hello")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json() == {
            "file_name": "readme",
            "content": "# Hello",
        }

    def test_upload_file_duplicate_stem(self, test_client):
        response1 = upload(test_client, "duplicate_test.txt", "test content")
        response2 = upload(test_client, "duplicate_test.md", "new content")

        assert response1.status_code == status.HTTP_201_CREATED
        assert response2.status_code == status.HTTP_409_CONFLICT
        assert response2.json()["detail"] == "File 'duplicate_test' already exists"

    def test_upload_file_unsupported_format(self, test_client):
        response = upload(test_client, "image.png", b"png")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == "Unsupported file format: .png"

    def test_upload_file_invalid_chars(self, test_client):
        for invalid_name in [
            "test/file.txt",
            "test\\file.txt",
            "test:file.txt",
            "test*file.txt",
            "test?file.txt",
            "test<file.txt",
            "test>file.txt",
            "test|file.txt",
        ]:
            response = upload(test_client, invalid_name, "content")

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert response.json()["detail"] == (
                "File name cannot contain path or reserved characters"
            )

    def test_upload_file_missing_file_field(self, test_client):
        response = test_client.post("/")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_full_workflow(self, test_client):
        file_name = "workflow_test"
        content = "Initial content"

        create_response = upload(test_client, f"{file_name}.txt", content)
        list_response = test_client.get("/")
        read_response = test_client.get(f"/{file_name}")
        duplicate_response = upload(test_client, f"{file_name}.md", "New content")

        assert create_response.status_code == status.HTTP_201_CREATED
        assert list_response.status_code == status.HTTP_200_OK
        assert file_name in list_response.json()["files"]
        assert read_response.status_code == status.HTTP_200_OK
        assert read_response.json()["content"] == content
        assert duplicate_response.status_code == status.HTTP_409_CONFLICT

    def test_multiple_requests(self, test_client):
        for i in range(5):
            response = upload(test_client, f"multi_test_{i}.txt", f"Content {i}")
            assert response.status_code == status.HTTP_201_CREATED

        response = test_client.get("/")

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["files"] == [f"multi_test_{i}" for i in range(5)]
