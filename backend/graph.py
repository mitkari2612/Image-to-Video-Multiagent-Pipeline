from typing import Dict, Any

from nodes import (
    intent_parser,
    image_analyzer,
    storyboard_writer,
    script_generator,
    compiler_fixer,
    renderer
)


def create_pipeline():
    """Create simple sequential pipeline for video generation."""
    
    def run_pipeline(state: Dict[str, Any]) -> Dict[str, Any]:
        """Run all pipeline nodes sequentially."""
        # Node 1: Intent Parser
        state = intent_parser(state)
        
        # Node 2: Image Analyzer
        state = image_analyzer(state)
        
        # Node 3: Storyboard Writer
        state = storyboard_writer(state)
        
        # Node 4: Script Generator
        state = script_generator(state)
        
        # Node 5: Compiler & Fixer (with retry logic)
        max_retries = 3
        for i in range(max_retries):
            state = compiler_fixer(state)
            if not state.get("compile_error"):
                break
        
        # Node 6: Renderer
        state = renderer(state)
        
        return state
    
    return run_pipeline