import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import shutil
import json

from config import UPLOAD_DIR, OUTPUT_DIR
from graph import create_pipeline
from rag import initialize_rag

# Initialize RAG on startup
initialize_rag()

app = FastAPI(title="Image-to-Video Pipeline", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GenerateRequest(BaseModel):
    image_folder: str
    user_prompt: str


class GenerateResponse(BaseModel):
    storyboard: List[Dict[str, Any]]
    script: str
    video_path: Optional[str]
    pipeline_state: Dict[str, Any]


@app.get("/")
async def root():
    return {"status": "running", "message": "Image-to-Video Pipeline API"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/generate", response_model=GenerateResponse)
async def generate_video(request: GenerateRequest):
    """Generate video from images and user prompt."""
    try:
        # Validate image folder
        if not os.path.exists(request.image_folder):
            raise HTTPException(status_code=400, detail=f"Image folder not found: {request.image_folder}")
        
        # Create pipeline
        pipeline = create_pipeline()
        
        # Prepare initial state
        initial_state = {
            "images": [],
            "intent": None,
            "analysis": [],
            "storyboard": [],
            "script": "",
            "compile_error": None,
            "retry_count": 0,
            "output_video": None,
            "image_folder": request.image_folder,
            "user_prompt": request.user_prompt
        }
        
        # Run pipeline
        result = pipeline(initial_state)
        
        # Prepare response
        response = GenerateResponse(
            storyboard=result.get("storyboard", []),
            script=result.get("script", ""),
            video_path=result.get("output_video"),
            pipeline_state={
                "images": result.get("images", []),
                "intent": result.get("intent"),
                "analysis_count": len(result.get("analysis", [])),
                "storyboard_count": len(result.get("storyboard", [])),
                "compile_error": result.get("compile_error"),
                "retry_count": result.get("retry_count", 0)
            }
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload-images")
async def upload_images(files: List[UploadFile] = File(...)):
    """Upload images to the server."""
    uploaded_files = []
    
    for file in files:
        # Validate file type
        if not file.content_type.startswith("image/"):
            continue
        
        # Save file
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        uploaded_files.append(file_path)
    
    return {
        "message": f"Uploaded {len(uploaded_files)} images",
        "files": uploaded_files,
        "folder": UPLOAD_DIR
    }


@app.get("/image")
async def get_image(path: str):
    """Serve image files."""
    try:
        # Decode the path
        image_path = path
        
        # Check if file exists
        if not os.path.exists(image_path):
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Determine content type
        ext = os.path.splitext(image_path)[1].lower()
        content_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.webp': 'image/webp',
            '.gif': 'image/gif'
        }
        content_type = content_types.get(ext, 'image/jpeg')
        
        from fastapi.responses import FileResponse
        return FileResponse(image_path, media_type=content_type)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Image not found: {str(e)}")


@app.get("/video")
async def get_video(path: str):
    """Serve video files."""
    try:
        # Decode the path
        video_path = path
        
        # Check if file exists
        if not os.path.exists(video_path):
            raise HTTPException(status_code=404, detail="Video not found")
        
        from fastapi.responses import FileResponse
        return FileResponse(video_path, media_type="video/mp4")
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Video not found: {str(e)}")


@app.get("/storyboard/{video_id}")
async def get_storyboard(video_id: str):
    """Get storyboard for a generated video."""
    metadata_path = os.path.join(OUTPUT_DIR, "video_metadata.json")
    
    if not os.path.exists(metadata_path):
        raise HTTPException(status_code=404, detail="Video metadata not found")
    
    with open(metadata_path, "r") as f:
        metadata = json.load(f)
    
    return metadata


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)