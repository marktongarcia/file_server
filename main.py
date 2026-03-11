from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse


BASE_DIR = Path(__file__).resolve().parent
FILES_DIR = BASE_DIR / "files"
FILES_DIR.mkdir(exist_ok=True)

app = FastAPI(title="FastAPI File Server")


def normalize_filename(filename: str) -> str:
    if not filename:
        raise HTTPException(status_code=400, detail="Filename is required.")

    cleaned = Path(filename).name
    if cleaned in {"", ".", ".."} or cleaned != filename:
        raise HTTPException(status_code=400, detail="Invalid filename.")

    return cleaned


def get_file_path(filename: str) -> Path:
    safe_name = normalize_filename(filename)
    files_root = FILES_DIR.resolve()
    file_path = (files_root / safe_name).resolve()

    if file_path.parent != files_root:
        raise HTTPException(status_code=400, detail="Invalid filename.")

    return file_path


@app.get("/")
async def root() -> dict[str, object]:
    return {
        "message": "FastAPI file server",
        "upload_endpoint": "/upload",
        "download_endpoint": "/download/{filename}",
        "download_query_endpoint": "/download?file={filename}",
        "list_endpoint": "/files",
    }


@app.get("/files")
async def list_files() -> dict[str, list[dict[str, int | str]]]:
    files = []

    for file_path in sorted(FILES_DIR.iterdir()):
        if file_path.is_file():
            files.append(
                {
                    "name": file_path.name,
                    "size": file_path.stat().st_size,
                }
            )

    return {"files": files}


def build_download_response(filename: str) -> FileResponse:
    file_path = get_file_path(filename)

    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found.")

    return FileResponse(path=file_path, filename=file_path.name)


@app.post("/upload", status_code=201)
async def upload_file(file: UploadFile = File(...), overwrite: bool = False) -> dict[str, object]:
    filename = normalize_filename(file.filename or "")
    destination = get_file_path(filename)

    if destination.exists() and not overwrite:
        raise HTTPException(
            status_code=409,
            detail="File already exists. Use overwrite=true to replace it.",
        )

    try:
        with destination.open("wb") as output_file:
            while chunk := await file.read(1024 * 1024):
                output_file.write(chunk)
    finally:
        await file.close()

    return {
        "filename": filename,
        "size": destination.stat().st_size,
        "download_url": f"/download/{filename}",
        "download_url_query": f"/download?file={filename}",
    }


@app.get("/download/{filename}")
async def download_file(filename: str) -> FileResponse:
    return build_download_response(filename)


@app.get("/download")
async def download_file_by_query(filename: str = Query(..., alias="file")) -> FileResponse:
    return build_download_response(filename)


@app.get("/files/{filename}")
async def download_file_legacy(filename: str) -> FileResponse:
    return build_download_response(filename)
