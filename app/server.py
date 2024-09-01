import shutil
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from app.merger import merge_files

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def ensure_folders_exist():
    folders = ["data", "data/main", "data/toMerge"]
    for folder in folders:
        Path(folder).mkdir(parents=True, exist_ok=True)


@app.get("/ping")
async def hello_world():
    return {"message": "pong"}


@app.post("/api/merge-db")
async def merge_db(main: UploadFile = File(...), toMerge: UploadFile = File(...)):
    try:
        ensure_folders_exist()

        main_path = Path("data") / "main.zip"
        with main_path.open("wb") as buffer:
            shutil.copyfileobj(main.file, buffer)

        toMerge_path = Path("data") / "toMerge.zip"
        with toMerge_path.open("wb") as buffer:
            shutil.copyfileobj(toMerge.file, buffer)

        result = merge_files()

        if result:
            merged_file_path = Path("data") / "merged.jwlibrary"
            if merged_file_path.exists():
                return FileResponse(
                    path=merged_file_path,
                    filename="merged.jwlibrary",
                    media_type="application/octet-stream",
                    headers={
                        "Content-Disposition": "attachment; filename=merged.jwlibrary"
                    },
                )
            else:
                raise HTTPException(status_code=500, detail="Merged file not found")
        else:
            raise HTTPException(status_code=500, detail="Error merging files")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
