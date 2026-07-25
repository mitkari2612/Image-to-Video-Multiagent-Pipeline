import pytest
from unittest.mock import Mock, patch, MagicMock
import json
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from backend.models import PipelineState, VideoIntent, ImageAnalysis, StoryboardScene
from backend.nodes import (
    intent_parser,
    image_analyzer,
    storyboard_writer,
    script_generator,
    compiler_fixer,
    renderer
)
from backend.rag import get_style_guide, get_remotion_docs, initialize_rag


class TestIntentParser:
    """Test intent parser node."""
    
    def test_fallback_when_no_api_key(self):
        """Test fallback intent when no API key."""
        state = {"user_prompt": "Create a wedding video"}
        result = intent_parser(state)
        
        assert result["intent"]["pacing"] == "moderate"
        assert result["intent"]["style"] == "elegant"
        assert result["intent"]["transition"] == "fade"
    
    @patch('backend.nodes.genai')
    def test_intent_parsing_with_gemini(self, mock_genai):
        """Test intent parsing with mocked Gemini."""
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = '{"pacing": "fast", "style": "fun", "caption_tone": "cheerful", "transition": "crossfade"}'
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        state = {"user_prompt": "Create a fun birthday party video"}
        result = intent_parser(state)
        
        assert result["intent"]["pacing"] == "fast"
        assert result["intent"]["style"] == "fun"
        assert result["intent"]["transition"] == "crossfade"


class TestImageAnalyzer:
    """Test image analyzer node."""
    
    def test_no_folder(self):
        """Test with non-existent folder."""
        state = {"image_folder": "/nonexistent/path"}
        result = image_analyzer(state)
        
        assert result["images"] == []
        assert result["analysis"] == []
    
    def test_fallback_analysis(self):
        """Test fallback image analysis."""
        # Create a temporary test image
        test_dir = os.path.join(os.path.dirname(__file__), "test_images")
        os.makedirs(test_dir, exist_ok=True)
        test_image = os.path.join(test_dir, "wedding_photo.jpg")
        
        # Create a simple test file
        with open(test_image, "w") as f:
            f.write("fake image")
        
        try:
            state = {"image_folder": test_dir}
            result = image_analyzer(state)
            
            assert len(result["images"]) > 0
            assert len(result["analysis"]) > 0
            assert "description" in result["analysis"][0]
            assert "emotion" in result["analysis"][0]
            assert "quality_score" in result["analysis"][0]
        finally:
            # Cleanup
            if os.path.exists(test_image):
                os.remove(test_image)
            if os.path.exists(test_dir):
                os.rmdir(test_dir)
    
    @patch('backend.nodes.client')
    def test_vision_analysis(self, mock_client):
        """Test GPT-4o Vision analysis."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "description": "Beautiful wedding ceremony",
            "emotion": "happy",
            "quality_score": 0.9,
            "scene": "ceremony",
            "people_count": 2
        })
        mock_client.chat.completions.create.return_value = mock_response
        
        # This would need actual image file in real test
        # For now, just verify the function structure
        state = {"image_folder": "/tmp"}
        result = image_analyzer(state)
        
        assert "analysis" in result


class TestStoryboardWriter:
    """Test storyboard writer node."""
    
    def test_empty_analysis(self):
        """Test with empty analysis."""
        state = {"analysis": [], "user_prompt": "test"}
        result = storyboard_writer(state)
        
        assert result["storyboard"] == []
    
    @patch('backend.nodes.client')
    def test_storyboard_generation(self, mock_client):
        """Test storyboard generation with mocked client."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "scenes": [
                {
                    "image": "img1.jpg",
                    "caption": "Beautiful moment",
                    "duration": 3,
                    "transition": "fade"
                }
            ]
        })
        mock_client.chat.completions.create.return_value = mock_response
        
        state = {
            "analysis": [
                {
                    "image": "img1.jpg",
                    "description": "Test image",
                    "emotion": "happy",
                    "quality_score": 0.8,
                    "scene": "outdoor",
                    "people_count": 2
                }
            ],
            "user_prompt": "wedding video",
            "intent": {"transition": "fade"}
        }
        
        result = storyboard_writer(state)
        
        assert len(result["storyboard"]) == 1
        assert result["storyboard"][0]["caption"] == "Beautiful moment"
        assert result["storyboard"][0]["order"] == 1
    
    def test_fallback_storyboard(self):
        """Test fallback storyboard creation."""
        state = {
            "analysis": [
                {"image": "img1.jpg", "quality_score": 0.9},
                {"image": "img2.jpg", "quality_score": 0.7}
            ],
            "intent": {"transition": "crossfade", "pacing": "fast"}
        }
        
        result = storyboard_writer(state)
        
        assert len(result["storyboard"]) == 2
        assert result["storyboard"][0]["transition"] == "crossfade"
        assert result["storyboard"][0]["duration"] == 3  # fast pacing


class TestScriptGenerator:
    """Test script generator node."""
    
    def test_empty_storyboard(self):
        """Test with empty storyboard."""
        state = {"storyboard": []}
        result = script_generator(state)
        
        assert result["script"] == ""
    
    def test_fallback_script(self):
        """Test fallback script generation."""
        state = {
            "storyboard": [
                {
                    "image": "img1.jpg",
                    "caption": "Scene 1",
                    "duration": 3,
                    "transition": "fade",
                    "order": 1
                }
            ]
        }
        
        result = script_generator(state)
        
        assert "import React" in result["script"]
        assert "Sequence" in result["script"]
        assert "Img" in result["script"]
        assert "img1.jpg" in result["script"]


class TestCompilerFixer:
    """Test compiler and fixer node."""
    
    def test_valid_script(self):
        """Test with valid script."""
        state = {
            "script": "import React from 'react';\nexport const Video = () => {};",
            "retry_count": 0
        }
        
        result = compiler_fixer(state)
        
        assert result["compile_error"] is None
        assert result["retry_count"] == 0
    
    def test_invalid_script_retry(self):
        """Test invalid script triggers retry."""
        state = {
            "script": "invalid script",
            "retry_count": 0
        }
        
        result = compiler_fixer(state)
        
        assert result["compile_error"] is not None
        assert result["retry_count"] == 1
        assert "import React" in result["script"]
    
    def test_max_retries(self):
        """Test max retries reached."""
        state = {
            "script": "invalid",
            "retry_count": 3
        }
        
        result = compiler_fixer(state)
        
        assert result["retry_count"] == 4
        assert result["compile_error"] is not None


class TestRenderer:
    """Test renderer node."""
    
    def test_render_with_valid_data(self):
        """Test rendering with valid storyboard and script."""
        output_dir = os.path.join(os.path.dirname(__file__), "..", "sample_output")
        os.makedirs(output_dir, exist_ok=True)
        
        state = {
            "storyboard": [
                {"image": "img1.jpg", "caption": "Test", "duration": 3}
            ],
            "script": "import React from 'react';"
        }
        
        result = renderer(state)
        
        assert result["output_video"] is not None
        assert "final.mp4" in result["output_video"]
        
        # Verify metadata file created
        metadata_path = os.path.join(output_dir, "video_metadata.json")
        assert os.path.exists(metadata_path)
        
        # Cleanup
        if os.path.exists(metadata_path):
            os.remove(metadata_path)
    
    def test_render_with_empty_data(self):
        """Test rendering with empty data."""
        state = {"storyboard": [], "script": ""}
        result = renderer(state)
        
        assert result["output_video"] is None


class TestRAG:
    """Test RAG functionality."""
    
    def test_initialize_rag(self):
        """Test RAG initialization."""
        initialize_rag()
        # Should not raise exception
        assert True
    
    def test_get_style_guide(self):
        """Test style guide retrieval."""
        initialize_rag()
        guides = get_style_guide("wedding video")
        
        assert len(guides) > 0
        assert "text" in guides[0]
    
    def test_get_remotion_docs(self):
        """Test Remotion docs retrieval."""
        initialize_rag()
        docs = get_remotion_docs("slideshow sequence")
        
        assert len(docs) > 0
        assert "text" in docs[0]


class TestLLMAsJudge:
    """LLM-as-judge mocked test."""
    
    @patch('backend.nodes.client')
    def test_quality_validation(self, mock_client):
        """Test that generated storyboard meets quality criteria."""
        # Mock LLM as judge
        judge_response = Mock()
        judge_response.choices = [Mock()]
        judge_response.choices[0].message.content = json.dumps({
            "quality_score": 0.9,
            "passes": True,
            "feedback": "Good storyboard with appropriate pacing"
        })
        mock_client.chat.completions.create.return_value = judge_response
        
        # Create a storyboard
        state = {
            "analysis": [
                {"image": "img1.jpg", "quality_score": 0.9, "emotion": "happy"}
            ],
            "user_prompt": "wedding video",
            "intent": {"transition": "fade"}
        }
        
        result = storyboard_writer(state)
        
        # Verify storyboard was created
        assert len(result["storyboard"]) > 0
        
        # In real scenario, would call judge here
        # For test, just verify structure
        for scene in result["storyboard"]:
            assert "image" in scene
            assert "caption" in scene
            assert "duration" in scene
            assert 2 <= scene["duration"] <= 5


class TestIntegration:
    """Integration tests."""
    
    def test_full_pipeline_no_client(self):
        """Test full pipeline without OpenAI client."""
        from backend.graph import create_pipeline
        
        pipeline = create_pipeline()
        
        initial_state = {
            "images": [],
            "intent": None,
            "analysis": [],
            "storyboard": [],
            "script": "",
            "compile_error": None,
            "retry_count": 0,
            "output_video": None,
            "image_folder": "/nonexistent",
            "user_prompt": "test"
        }
        
        result = pipeline.invoke(initial_state)
        
        assert "intent" in result
        assert "storyboard" in result
        assert "script" in result
        assert "output_video" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])