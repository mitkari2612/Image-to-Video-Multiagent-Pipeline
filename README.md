# Image-to-Video Multiagent Pipeline

A production-ready pipeline that transforms static images into engaging videos using AI. Built with FastAPI, LangGraph, and Remotion.

## Architecture

```
┌─────────────┐
│   User      │
│   Prompt    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│                   LangGraph Pipeline                     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐    ┌──────────────┐                  │
│  │ Intent       │───▶│ Image        │                  │
│  │ Parser       │    │ Analyzer     │                  │
│  │ (Gemini)     │    │ (Gemini      │                  │
│  │              │    │  Vision)     │                  │
│  └──────────────┘    └──────┬───────┘                  │
│                             │                            │
│                             ▼                            │
│                    ┌──────────────────┐                 │
│                    │ Storyboard       │                 │
│                    │ Writer           │                 │
│                    │ (Gemini + RAG)   │                 │
│                    └────────┬─────────┘                 │
│                             │                            │
│                             ▼                            │
│                    ┌──────────────────┐                 │
│                    │ Script           │                 │
│                    │ Generator        │                 │
│                    │ (Gemini + RAG)   │                 │
│                    └────────┬─────────┘                 │
│                             │                            │
│                             ▼                            │
│                    ┌──────────────────┐                 │
│                    │ Compiler &       │                 │
│                    │ Fixer            │                 │
│                    │ (Retry x3)       │                 │
│                    └────────┬─────────┘                 │
│                             │                            │
│                             ▼                            │
│                    ┌──────────────────┐                 │
│                    │ Renderer         │                 │
│                    │ (Remotion)       │                 │
│                    └──────────────────┘                 │
│                                                         │
└─────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────┐
│   Output    │
│   Video     │
│   (MP4)     │
└─────────────┘
```

## LangGraph State Graph

```
                    ┌──────────────┐
                    │   START      │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ Intent       │
                    │ Parser       │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ Image        │
                    │ Analyzer     │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ Storyboard   │
                    │ Writer       │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ Script       │
                    │ Generator    │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ Compiler &   │
                    │ Fixer        │
                    └──────┬───────┘
                           │
                    ┌──────┴───────┐
                    │              │
              (Error)│              │(Success)
                    │              │
                    ▼              ▼
            ┌──────────────┐  ┌──────────────┐
            │ Retry        │  │ Renderer     │
            │ (max 3x)     │  │              │
            └──────┬───────┘  └──────┬───────┘
                   │                  │
                   └────────┬─────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │     END      │
                     └──────────────┘
```

## Tech Stack

- **Backend**: Python 3.11, FastAPI, LangGraph, LangChain
- **AI**: Google Gemini 1.5 Flash (text + vision)
- **RAG**: ChromaDB (local), SentenceTransformers embeddings
- **Frontend**: React, TypeScript, Vite
- **Video**: Remotion
- **Testing**: Pytest

## Project Structure

```
├── backend/
│   ├── config.py          # Configuration and environment variables
│   ├── models.py          # Pydantic models and TypedDict state
│   ├── rag.py             # ChromaDB RAG implementation
│   ├── nodes.py           # LangGraph pipeline nodes
│   ├── graph.py           # LangGraph StateGraph definition
│   └── main.py            # FastAPI application
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx        # Main React component
│   │   └── main.tsx       # React entry point
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
│
├── remotion/
│   ├── src/
│   │   ├── Video.tsx      # Remotion video component
│   │   ├── Root.tsx       # Remotion root component
│   │   └── index.ts       # Remotion entry point
│   ├── package.json
│   └── tsconfig.json
│
├── vector_db/             # ChromaDB persistent storage
├── tests/
│   └── test_pipeline.py   # Pytest tests
├── sample_output/         # Generated videos
├── Dataset images/        # Sample images
│
├── requirements.txt
├── .env.example
└── README.md
```

## Model Choice

**Why Google Gemini?**
- Free tier available (Google AI Studio)
- Single model for all text generation (gemini-1.5-flash)
- Gemini Vision for image analysis (built-in multimodal)
- Fast inference times
- No dependency conflicts

**No multiple expensive models** - We use Gemini for:
1. Intent parsing (gemini-1.5-flash)
2. Storyboard generation (gemini-1.5-flash)
3. Script generation (gemini-1.5-flash)
4. Image analysis (gemini-1.5-flash Vision)

## RAG Explanation

We use **local ChromaDB** with two collections:

### 1. Style Guides Collection
- **Purpose**: Provides video style recommendations based on event type
- **Content**: Wedding, birthday, corporate, travel guides
- **Usage**: Retrieved during storyboard generation to match video tone

### 2. Remotion Docs Collection
- **Purpose**: Provides Remotion component documentation
- **Content**: Sequence, Img, AbsoluteFill, interpolate usage
- **Usage**: Retrieved during script generation for accurate code

**Embedding Model**: SentenceTransformers `all-MiniLM-L6-v2` (fast, lightweight)

**Seeding**: Collections are automatically seeded on first run if empty.

## Installation

### Prerequisites
- Python 3.11+
- Node.js 18+
- Google AI Studio API key (free at https://aistudio.google.com)

### Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

### Frontend Setup

```bash
cd frontend
npm install
```

### Remotion Setup

```bash
cd remotion
npm install
```

## Running the Application

### 1. Start Backend Server

```bash
cd backend
python main.py
# Server runs on http://localhost:8000
```

### 2. Start Frontend (in new terminal)

```bash
cd frontend
npm run dev
# Frontend runs on http://localhost:3000
```

### 3. Access the Application

Open browser to `http://localhost:3000`

## Usage

1. **Enter Image Folder Path**: Point to folder containing images (e.g., `./Dataset images`)
2. **Enter Video Prompt**: Describe the video you want (e.g., "Create a wedding video with elegant transitions")
3. **Click "Generate Video"**
4. View:
   - Pipeline state (images found, analyzed, etc.)
   - Generated storyboard
   - Remotion script
   - Output video path

## API Endpoints

### POST /generate
Generate video from images and prompt.

**Request:**
```json
{
  "image_folder": "./Dataset images",
  "user_prompt": "Create a wedding video with elegant transitions"
}
```

**Response:**
```json
{
  "storyboard": [
    {
      "image": "./Dataset images/photo1.jpg",
      "caption": "Beautiful ceremony",
      "duration": 3,
      "transition": "fade",
      "order": 1
    }
  ],
  "script": "import React from 'react';\n...",
  "video_path": "./sample_output/final.mp4",
  "pipeline_state": {
    "images": [...],
    "intent": {...},
    "analysis_count": 5,
    "storyboard_count": 5,
    "retry_count": 0
  }
}
```

### POST /upload-images
Upload images to server.

### GET /storyboard/{video_id}
Get storyboard for generated video.

## Testing

```bash
# Run all tests
pytest tests/test_pipeline.py -v

# Run specific test class
pytest tests/test_pipeline.py::TestIntentParser -v

# Run with coverage
pytest tests/test_pipeline.py --cov=backend
```

### Test Coverage

- ✅ Intent parsing (with/without Gemini API)
- ✅ Image analysis (fallback and Vision API)
- ✅ Storyboard generation
- ✅ Script generation
- ✅ Compiler and fixer (retry logic)
- ✅ Renderer
- ✅ RAG initialization and retrieval
- ✅ LLM-as-judge validation
- ✅ Full pipeline integration

## Pipeline Nodes

### 1. Intent Parser
- **Input**: User prompt
- **Output**: VideoIntent (pacing, style, caption_tone, transition)
- **Model**: Gemini 1.5 Flash
- **Fallback**: Default values if no API key

### 2. Image Analyzer
- **Input**: Image folder path
- **Output**: List of ImageAnalysis (description, emotion, quality_score, scene, people_count)
- **Model**: Gemini 1.5 Flash Vision (with fallback to metadata analysis)
- **Selection**: Top 10 images by quality score

### 3. Storyboard Writer
- **Input**: Image analysis + user prompt
- **Output**: Storyboard (scenes with captions, durations, transitions)
- **RAG**: Retrieves style guides from ChromaDB
- **Model**: Gemini 1.5 Flash

### 4. Script Generator
- **Input**: Storyboard
- **Output**: Remotion TypeScript code
- **RAG**: Retrieves Remotion documentation from ChromaDB
- **Components**: Sequence, Img, AbsoluteFill, interpolate
- **Model**: Gemini 1.5 Flash

### 5. Compiler & Fixer
- **Input**: Generated script
- **Output**: Validated/fixed script
- **Logic**: Validates structure, retries up to 3 times
- **Fallback**: Returns structured error if max retries reached

### 6. Renderer
- **Input**: Validated script + storyboard
- **Output**: final.mp4 path
- **Implementation**: Creates metadata file (actual Remotion rendering requires full project setup)

### 5. Compiler & Fixer
- **Input**: Generated script
- **Output**: Validated/fixed script
- **Logic**: Validates structure, retries up to 3 times
- **Fallback**: Returns structured error if max retries reached

### 6. Renderer
- **Input**: Validated script + storyboard
- **Output**: final.mp4 path
- **Implementation**: Creates metadata file (actual Remotion rendering requires full project setup)

## State Management

```python
PipelineState = TypedDict({
    "images": List[str],           # List of image file paths
    "intent": Optional[Dict],      # VideoIntent parameters
    "analysis": List[Dict],        # ImageAnalysis results
    "storyboard": List[Dict],      # StoryboardScene list
    "script": str,                 # Generated Remotion code
    "compile_error": Optional[str], # Compilation errors
    "retry_count": int,            # Number of retries
    "output_video": Optional[str]  # Path to final video
})
```

## Known Limitations

1. **Video Rendering**: Actual MP4 rendering requires full Remotion project setup with all dependencies. Current implementation generates script and metadata.

2. **Image Analysis**: Gemini Vision requires valid image files. Fallback uses filename heuristics.

3. **ChromaDB**: Requires first-run seeding (automatic). Large image collections may slow down embedding generation.

4. **No Authentication**: API is open (suitable for local development only).

5. **No Cloud Deployment**: Designed for local execution only.

6. **Memory**: No persistent agent memory (stateless pipeline).

7. **Concurrent Requests**: Not optimized for concurrent video generation (single-threaded).

## Example Prompts

### Wedding
```
Create an elegant wedding video with soft fade transitions and warm captions. 
Focus on emotional moments and beautiful details.
```

### Birthday
```
Create a fun birthday party video with upbeat crossfade transitions and cheerful captions. 
Include party moments and happy expressions.
```

### Corporate
```
Create a professional corporate video with smooth transitions and formal captions. 
Focus on business moments and professional settings.
```

## Troubleshooting

### Backend won't start
- Check Python version: `python --version` (need 3.11+)
- Verify dependencies: `pip install -r requirements.txt`
- Check .env file exists with GOOGLE_API_KEY

### Frontend won't start
- Check Node version: `node --version` (need 18+)
- Run `npm install` in frontend directory
- Verify backend is running on port 8000

### ChromaDB errors
- Delete `vector_db/chroma_db` folder and restart
- Check disk space

### Google AI Studio API errors
- Verify API key in .env
- Check API quota at https://aistudio.google.com
- Ensure Gemini API is enabled

## Development

### Adding New Style Guides
Edit `backend/rag.py` and add to `seed_style_guides()`:

```python
{
    "id": "new_type",
    "text": "Description of new video style...",
    "metadata": {"type": "new_type", "tone": "tone"}
}
```

### Adding New Pipeline Nodes
1. Add node function in `backend/nodes.py`
2. Add node to graph in `backend/graph.py`
3. Update `PipelineState` in `backend/models.py`

### Customizing Remotion Output
Edit `remotion/src/Video.tsx` to modify:
- Transitions
- Caption styles
- Animation effects
- Video dimensions

## License

MIT

## Contributing

1. Fork the repository
2. Create feature branch
3. Run tests: `pytest tests/`
4. Submit pull request

## Contact

For questions or issues, please open a GitHub issue.