from pathlib import Path

from fastapi import FastAPI, HTTPException
import uvicorn

main_app = FastAPI()


@main_app.get("/")
def get_file_list():
    path = Path(__file__).parent / "files"
    return [file.stem for file in path.iterdir()]


@main_app.get("/{file_name}")
def read_file(file_name: str):
    path = Path(__file__).parent / "files"
    try:
        file = path / file_name
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")

    with open(f"{file}.txt", "r", encoding="utf8") as f:
        return f.readline()


@main_app.post("/")
def post_file(file_id: int):
    return {"file_id": file_id}


if __name__ == "__main__":
    uvicorn.run(
        "main:main_app",
        host="localhost",
        port=8000,
        reload=True,
    )

# Доделать весь функционал
# добавить валидацию pandentic
# тесты