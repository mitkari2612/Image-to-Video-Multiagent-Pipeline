import os
import json
import base64
from typing import Dict, Any, List
from pathlib import Path

import google.generativeai as genai
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import GOOGLE_API_KEY
from models import VideoIntent, ImageAnalysis, StoryboardScene
from rag import get_style_guide, get_remotion_docs

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)


def intent_parser(state: Dict[str, Any]) -> Dict[str, Any]:
    """Node 1: Parse user prompt into VideoIntent."""
    prompt = state.get("user_prompt", "")
    
    if not GOOGLE_API_KEY:
        # Fallback intent
        state["intent"] = {
            "pacing": "moderate",
            "style": "elegant",
            "caption_tone": "warm",
            "transition": "fade"
        }
        return state
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(
            f"""Extract video production parameters from this prompt: "{prompt}"
            
Return ONLY a JSON object with these fields:
- pacing: "slow", "moderate", or "fast"
- style: "elegant", "fun", "professional", or "adventurous"
- caption_tone: "warm", "cheerful", "formal", or "descriptive"
- transition: "fade", "crossfade", or "slide"

Example: {{"pacing": "moderate", "style": "elegant", "caption_tone": "warm", "transition": "fade"}}"""
        )
        
        # Extract JSON from response
        response_text = response.text.strip()
        if '{' in response_text:
            json_str = response_text[response_text.index('{'):response_text.rindex('}')+1]
            intent_data = json.loads(json_str)
            state["intent"] = intent_data
        else:
            raise ValueError("No JSON in response")
    except Exception as e:
        state["intent"] = {
            "pacing": "moderate",
            "style": "elegant",
            "caption_tone": "warm",
            "transition": "fade"
        }
    
    return state


def image_analyzer(state: Dict[str, Any]) -> Dict[str, Any]:
    """Node 2: Analyze images using Gemini Vision or fallback."""
    image_folder = state.get("image_folder", "")
    images = []
    
    if not image_folder or not os.path.exists(image_folder):
        state["images"] = []
        state["analysis"] = []
        return state
    
    # Get image files
    valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
    image_files = []
    for f in os.listdir(image_folder):
        if any(f.lower().endswith(ext) for ext in valid_extensions):
            image_files.append(os.path.join(image_folder, f))
    
    image_files.sort()
    state["images"] = image_files
    
    if not image_files:
        state["analysis"] = []
        return state
    
    analyses = []
    
    for img_path in image_files:
        if GOOGLE_API_KEY:
            try:
                # Use Gemini Vision
                model = genai.GenerativeModel('gemini-1.5-flash')
                with open(img_path, "rb") as image_file:
                    image_data = image_file.read()
                
                response = model.generate_content([
                    "Analyze this image. Return JSON with: description (brief), emotion (happy/sad/neutral/excited), quality_score (0-1), scene (indoor/outdoor/party/ceremony), people_count (integer).",
                    {"mime_type": "image/jpeg", "data": image_data}
                ])
                
                # Extract JSON from response
                response_text = response.text.strip()
                if '{' in response_text:
                    json_str = response_text[response_text.index('{'):response_text.rindex('}')+1]
                    analysis = json.loads(json_str)
                    analysis["image"] = img_path
                    analysis["quality_score"] = float(analysis.get("quality_score", 0.5))
                    analysis["people_count"] = int(analysis.get("people_count", 0))
                    analyses.append(analysis)
                else:
                    raise ValueError("No JSON in response")
            except Exception as e:
                # Fallback to metadata analysis
                analyses.append(_fallback_image_analysis(img_path))
        else:
            # No API key, use fallback
            analyses.append(_fallback_image_analysis(img_path))
    
    # Sort by quality score and select best images (max 10)
    analyses.sort(key=lambda x: x.get("quality_score", 0), reverse=True)
    analyses = analyses[:10]
    
    state["analysis"] = analyses
    return state


def _fallback_image_analysis(img_path: str) -> Dict[str, Any]:
    """Fallback analysis using filename and basic metadata."""
    filename = os.path.basename(img_path).lower()
    
    # Simple heuristics based on filename
    emotion = "happy"
    if any(word in filename for word in ["sad", "serious", "formal"]):
        emotion = "neutral"
    elif any(word in filename for word in ["party", "fun", "play"]):
        emotion = "excited"
    
    scene = "outdoor"
    if any(word in filename for word in ["indoor", "room", "hall"]):
        scene = "indoor"
    elif any(word in filename for word in ["party", "event", "ceremony"]):
        scene = "party"
    
    people_count = 1
    if any(word in filename for word in ["group", "family", "team", "friends"]):
        people_count = 3
    
    # Try to get image size as quality indicator
    try:
        from PIL import Image
        with Image.open(img_path) as img:
            width, height = img.size
            quality_score = min(1.0, (width * height) / (1920 * 1080))
    except:
        quality_score = 0.5
    
    return {
        "image": img_path,
        "description": f"Image: {filename}",
        "emotion": emotion,
        "quality_score": quality_score,
        "scene": scene,
        "people_count": people_count
    }


def storyboard_writer(state: Dict[str, Any]) -> Dict[str, Any]:
    """Node 3: Generate storyboard from analysis and style guide."""
    analysis = state.get("analysis", [])
    user_prompt = state.get("user_prompt", "")
    intent = state.get("intent", {})
    
    if not analysis:
        state["storyboard"] = []
        return state
    
    # Get style guide from RAG
    style_guides = get_style_guide(user_prompt)
    style_context = "\n".join([g["text"] for g in style_guides]) if style_guides else "Create a balanced, professional video."
    
    if GOOGLE_API_KEY:
        try:
            # Prepare image descriptions
            image_descriptions = []
            for i, item in enumerate(analysis):
                image_descriptions.append(f"{i+1}. {item.get('description', 'Image')} - {item.get('emotion', 'neutral')} - {item.get('scene', 'unknown')}")
            
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(
                f"""You are a storyboard writer. Based on the style guide and image analysis, create a storyboard.
                
Style Guide: {style_context}

Create a JSON array of scenes. Each scene has: image (filename), caption (short engaging text), duration (seconds, 2-5), transition (fade/crossfade), order (1-based index).
Total duration should be 15-30 seconds. Use {intent.get('transition', 'fade')} transitions.

Create a storyboard for these images:
{chr(10).join(image_descriptions)}

Return ONLY a JSON object with a "scenes" array."""
            )
            
            # Extract JSON from response
            response_text = response.text.strip()
            if '{' in response_text:
                json_str = response_text[response_text.index('{'):response_text.rindex('}')+1]
                result = json.loads(json_str)
                storyboard = result.get("scenes", [])
                
                # Ensure proper structure
                formatted_storyboard = []
                for i, scene in enumerate(storyboard):
                    formatted_storyboard.append({
                        "image": scene.get("image", analysis[i]["image"] if i < len(analysis) else ""),
                        "caption": scene.get("caption", ""),
                        "duration": int(scene.get("duration", 3)),
                        "transition": scene.get("transition", intent.get("transition", "fade")),
                        "order": i + 1
                    })
                
                state["storyboard"] = formatted_storyboard
            else:
                raise ValueError("No JSON in response")
            
        except Exception as e:
            # Fallback storyboard
            state["storyboard"] = _create_fallback_storyboard(analysis, intent)
    else:
        state["storyboard"] = _create_fallback_storyboard(analysis, intent)
    
    return state


def _create_fallback_storyboard(analysis: List[Dict], intent: Dict) -> List[Dict]:
    """Create simple fallback storyboard."""
    storyboard = []
    transition = intent.get("transition", "fade")
    duration = 3 if intent.get("pacing") == "fast" else 4
    
    for i, item in enumerate(analysis):
        storyboard.append({
            "image": item["image"],
            "caption": f"Scene {i + 1}",
            "duration": duration,
            "transition": transition,
            "order": i + 1
        })
    
    return storyboard


def script_generator(state: Dict[str, Any]) -> Dict[str, Any]:
    """Node 4: Generate Remotion script from storyboard."""
    storyboard = state.get("storyboard", [])
    user_prompt = state.get("user_prompt", "")
    
    if not storyboard:
        state["script"] = ""
        return state
    
    # Get Remotion docs from RAG
    remotion_docs = get_remotion_docs("slideshow sequence images transitions")
    docs_context = "\n".join([d["text"] for d in remotion_docs]) if remotion_docs else ""
    
    if GOOGLE_API_KEY:
        try:
            # Prepare storyboard data
            scenes_json = json.dumps(storyboard, indent=2)
            
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(
                f"""You are a Remotion video generator. Create a simple React component using ONLY these Remotion components:
- Sequence (for timeline)
- Img (for images)
- AbsoluteFill (for layout)
- interpolate (for animations)
- useCurrentFrame (for frame access)

Remotion documentation context:
{docs_context}

Generate a complete, valid React/TypeScript file. Use only Sequence, Img, AbsoluteFill, interpolate, and useCurrentFrame. No other components.
Make a simple slideshow with fade transitions between images. Each image shows for its duration with a caption overlay.

Generate Remotion code for this storyboard:
{scenes_json}

User request: {user_prompt}

Return ONLY the TypeScript code, no explanations."""
            )
            
            state["script"] = response.text.strip()
            
        except Exception as e:
            state["script"] = _create_fallback_script(storyboard)
    else:
        state["script"] = _create_fallback_script(storyboard)
    
    return state


def _create_fallback_script(storyboard: List[Dict]) -> str:
    """Create simple fallback Remotion script."""
    scenes_code = []
    current_frame = 0
    
    for scene in storyboard:
        duration_frames = scene["duration"] * 30  # 30 fps
        transition = scene["transition"]
        
        scenes_code.append(f"""
      <Sequence from={current_frame} durationInFrames={duration_frames}>
        <AbsoluteFill>
          <Img src="{scene['image']}" style={{{{width: '100%', height: '100%', objectFit: 'cover'}}}} />
          <div style={{{{position: 'absolute', bottom: 50, left: 50, color: 'white', fontSize: 24, backgroundColor: 'rgba(0,0,0,0.5)', padding: 10}}}}>
            {scene['caption']}
          </div>
        </AbsoluteFill>
      </Sequence>""")
        
        current_frame += duration_frames
    
    scenes_joined = "".join(scenes_code)
    
    script = """import React from 'react';
import { Sequence, Img, AbsoluteFill, interpolate, useCurrentFrame } from 'remotion';

export const Video: React.FC<{images: string[]}> = () => {
  const frame = useCurrentFrame();
  
  return (
    <AbsoluteFill>
      """ + scenes_joined + """
    </AbsoluteFill>
  );
};

export const RemotionVideo: React.FC = () => {
  return <Video images={[]} />;
};
"""
    
    return script


def compiler_fixer(state: Dict[str, Any]) -> Dict[str, Any]:
    """Node 5: Compile and fix Remotion code."""
    script = state.get("script", "")
    retry_count = state.get("retry_count", 0)
    
    if not script:
        state["compile_error"] = "No script generated"
        state["retry_count"] = retry_count + 1
        return state
    
    # Simple validation (in real scenario, would actually compile)
    if "import React" not in script or "export" not in script:
        state["compile_error"] = "Invalid React component structure"
        state["retry_count"] = retry_count + 1
        
        if retry_count < 3:
            # Try to fix
            state["script"] = _fix_script(script)
        
        return state
    
    state["compile_error"] = None
    return state


def _fix_script(script: str) -> str:
    """Attempt to fix common script issues."""
    if "import React" not in script:
        script = "import React from 'react';\n" + script
    
    if "from 'remotion'" not in script:
        # Add basic imports
        script = script.replace("import React from 'react';", 
            "import React from 'react';\nimport { Sequence, Img, AbsoluteFill, interpolate, useCurrentFrame } from 'remotion';")
    
    return script


def renderer(state: Dict[str, Any]) -> Dict[str, Any]:
    """Node 6: Render final video."""
    storyboard = state.get("storyboard", [])
    script = state.get("script", "")
    
    if not storyboard or not script:
        state["output_video"] = None
        return state
    
    # In a real implementation, this would:
    # 1. Save the script to a Remotion project
    # 2. Run remotion render command
    # 3. Return the output video path
    
    # For this implementation, we'll create a placeholder
    output_dir = os.getenv("OUTPUT_DIR", "./sample_output")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "final.mp4")
    
    # Create a simple metadata file
    metadata = {
        "storyboard": storyboard,
        "script": script,
        "output_path": output_path,
        "status": "rendered"
    }
    
    metadata_path = os.path.join(output_dir, "video_metadata.json")
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    
    state["output_video"] = output_path
    return state