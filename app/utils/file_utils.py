from fastapi import HTTPException, UploadFile, status


async def read_upload_file(file: UploadFile, max_size_bytes: int = 10 * 1024 * 1024) -> bytes:
    content = await file.read()
    if len(content) > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Uploaded file exceeds the maximum allowed size.",
        )
    return content
