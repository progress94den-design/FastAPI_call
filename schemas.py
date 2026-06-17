from pydantic import BaseModel, Field


class FileCreate(BaseModel):
    file_name: str = Field(min_length=1, max_length=255)
    content: str = ""


class FileResponse(BaseModel):
    file_name: str
    content: str


class FileListResponse(BaseModel):
    files: list[str]
    count: int
