import uvicorn

from typing import TypeVar, Callable
from fastapi import FastAPI, HTTPException, status, UploadFile, File

from schemas import FileResponse, FileListResponse
from filemanager import file_manager

main_app = FastAPI()

T = TypeVar('T')

def safe_file_operation(operation_func: Callable[..., T], **kwargs) -> T:
    """
    Функция для безопасного выполнения операций с файлами
    Args:
        operation_func: функция для выполнения
        **kwargs: аргументы для передачи в функцию
    Returns:
        Результат выполнения функции
    Raises:
        HTTPException: с соответствующим статус кодом
    """
    try:
        return operation_func(**kwargs)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except FileExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Нет доступа к файлу: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка сервера: {str(e)}"
        )


@main_app.get("/", response_model=FileListResponse)
def get_file_list():
    """Возвращает список имён всех файлов в папке /files (без расширения)"""
    files = safe_file_operation(file_manager.get_all_files)
    return FileListResponse(files=files, count=len(files))


@main_app.get("/{file_name}", response_model=FileResponse)
def read_file(file_name: str):
    """Возвращает содержимое файла"""
    result = safe_file_operation(
        file_manager.get_file,
        file_name=file_name,
    )
    return FileResponse(**result)


@main_app.post("/upload/", status_code=status.HTTP_201_CREATED, response_model=FileResponse)
async def upload_file(file: UploadFile = File(...)):
    """Загрузка нового файла"""
    result = safe_file_operation(
        file_manager.post_file,
        file=file,
    )
    return FileResponse(**result)


if __name__ == "__main__":
    uvicorn.run(
        "main:main_app",
        host="localhost",
        port=8000,
        reload=True,
    )
