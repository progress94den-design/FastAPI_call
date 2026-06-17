from fastapi import status


class TestAPI:
    def test_get_file_list_empty(self, test_client):
        response = test_client.get("/")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"files": [], "count": 0}

    def test_get_file_list_with_files(self, test_client):
        test_client.post("/", json={"file_name": "file1", "content": "content1"})
        test_client.post("/", json={"file_name": "file2", "content": "content2"})

        response = test_client.get("/")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"files": ["file1", "file2"], "count": 2}

    def test_read_file_success(self, test_client):
        test_client.post("/", json={"file_name": "test", "content": "Hello World"})

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

    def test_create_file_success(self, test_client, sample_file_data):
        response = test_client.post("/", json=sample_file_data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json() == sample_file_data

    def test_create_file_empty_content(self, test_client):
        response = test_client.post("/", json={"file_name": "empty_file"})

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json() == {
            "file_name": "empty_file",
            "content": "",
        }

    def test_create_file_duplicate(self, test_client):
        test_data = {
            "file_name": "duplicate_test",
            "content": "test content",
        }

        response1 = test_client.post("/", json=test_data)
        response2 = test_client.post("/", json=test_data)

        assert response1.status_code == status.HTTP_201_CREATED
        assert response2.status_code == status.HTTP_409_CONFLICT
        assert response2.json()["detail"] == "File 'duplicate_test' already exists"

    def test_create_file_empty_string_name(self, test_client):
        response = test_client.post("/", json={"file_name": "", "content": "content"})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_create_file_spaces_only_name(self, test_client):
        response = test_client.post("/", json={"file_name": "   ", "content": "content"})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == "File name cannot be empty"

    def test_create_file_invalid_chars(self, test_client):
        for invalid_name in [
            "test/file",
            "test\\file",
            "test:file",
            "test*file",
            "test?file",
            "test<file",
            "test>file",
            "test|file",
        ]:
            response = test_client.post(
                "/",
                json={"file_name": invalid_name, "content": "content"},
            )

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert response.json()["detail"] == (
                "File name cannot contain path or reserved characters"
            )

    def test_create_file_missing_file_name(self, test_client):
        response = test_client.post("/", json={"content": "some content"})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_full_workflow(self, test_client):
        file_name = "workflow_test"
        content = "Initial content"

        create_response = test_client.post(
            "/",
            json={"file_name": file_name, "content": content},
        )
        list_response = test_client.get("/")
        read_response = test_client.get(f"/{file_name}")
        duplicate_response = test_client.post(
            "/",
            json={"file_name": file_name, "content": "New content"},
        )

        assert create_response.status_code == status.HTTP_201_CREATED
        assert list_response.status_code == status.HTTP_200_OK
        assert file_name in list_response.json()["files"]
        assert read_response.status_code == status.HTTP_200_OK
        assert read_response.json()["content"] == content
        assert duplicate_response.status_code == status.HTTP_409_CONFLICT

    def test_multiple_requests(self, test_client):
        for i in range(5):
            response = test_client.post(
                "/",
                json={"file_name": f"multi_test_{i}", "content": f"Content {i}"},
            )
            assert response.status_code == status.HTTP_201_CREATED

        response = test_client.get("/")

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["files"] == [f"multi_test_{i}" for i in range(5)]
