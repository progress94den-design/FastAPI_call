from typing import Callable, TypeVar

import uvicorn
from fastapi import FastAPI, HTTPException, status

import filemanager as filemanager_module
from schemas import FileCreate, FileListResponse, FileResponse


main_app = FastAPI(title="FastAPI File Manager")

T = TypeVar("T")


def safe_file_operation(operation_func: Callable[..., T], **kwargs) -> T:
    try:
        return operation_func(**kwargs)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except FileExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"No access to file: {exc}",
        ) from exc


@main_app.get("/", response_model=FileListResponse)
def get_file_list() -> FileListResponse:
    files = safe_file_operation(filemanager_module.file_manager.get_all_files)
    return FileListResponse(files=files, count=len(files))


@main_app.post("/", status_code=status.HTTP_201_CREATED, response_model=FileResponse)
def create_file(payload: FileCreate) -> FileResponse:
    result = safe_file_operation(
        filemanager_module.file_manager.create_file,
        file_name=payload.file_name,
        content=payload.content,
    )
    return FileResponse(**result)


@main_app.get("/{file_name}", response_model=FileResponse)
def read_file(file_name: str) -> FileResponse:
    result = safe_file_operation(
        filemanager_module.file_manager.get_file,
        file_name=file_name,
    )
    return FileResponse(**result)


if __name__ == "__main__":
    uvicorn.run(
        "main:main_app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
