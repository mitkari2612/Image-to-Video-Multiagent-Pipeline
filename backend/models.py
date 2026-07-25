from typing import TypedDict, List, Optional, Dict, Any
from pydantic import BaseModel


class VideoIntent(BaseModel):
    pacing: str = "moderate"
    style: str = "elegant"
    caption_tone: str = "warm"
    transition: str = "fade"


class ImageAnalysis(BaseModel):
    image: str
    description: str
    emotion: str
    quality_score: float
    scene: str
    people_count: int


class StoryboardScene(BaseModel):
    image: str
    caption: str
    duration: int
    transition: str
    order: int


class PipelineState(TypedDict):
    images: List[str]
    intent: Optional[Dict[str, Any]]
    analysis: List[Dict[str, Any]]
    storyboard: List[Dict[str, Any]]
    script: str
    compile_error: Optional[str]
    retry_count: int
    output_video: Optional[str]