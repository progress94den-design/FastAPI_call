from pydantic import BaseModel


class FileResponse(BaseModel):
    file_name: str
    content: str


class FileListResponse(BaseModel):
    files: list[str]
    count: int
