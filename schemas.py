from pydantic import BaseModel, Field


class FileBase(BaseModel):
    file_name: str = Field(min_length=1, max_length=255, description="Имя файла без расширения")
    content: str = Field(default="", description="Содержимое файла")


class FileResponse(FileBase):
    pass


class FileListResponse(BaseModel):
    files: list[str]
    count: int
