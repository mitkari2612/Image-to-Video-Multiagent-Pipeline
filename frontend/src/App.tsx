import React, { useState } from 'react';
import axios from 'axios';

interface Scene {
  image: string;
  caption: string;
  duration: number;
  transition: string;
  order: number;
}

interface PipelineState {
  images: string[];
  intent: any;
  analysis_count: number;
  storyboard_count: number;
  compile_error?: string;
  retry_count: number;
}

function App() {
  const [prompt, setPrompt] = useState('');
  const [imageFolder, setImageFolder] = useState('./Dataset images');
  const [loading, setLoading] = useState(false);
  const [storyboard, setStoryboard] = useState<Scene[]>([]);
  const [script, setScript] = useState('');
  const [videoPath, setVideoPath] = useState('');
  const [pipelineState, setPipelineState] = useState<PipelineState | null>(null);
  const [error, setError] = useState('');

  const handleGenerate = async () => {
    setLoading(true);
    setError('');
    setStoryboard([]);
    setScript('');
    setVideoPath('');
    setPipelineState(null);

    try {
      const response = await axios.post('http://localhost:8000/generate', {
        image_folder: imageFolder,
        user_prompt: prompt
      });

      setStoryboard(response.data.storyboard);
      setScript(response.data.script);
      setVideoPath(response.data.video_path);
      setPipelineState(response.data.pipeline_state);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: 20 }}>
      <h1>Image-to-Video Pipeline</h1>
      
      <div style={{ marginBottom: 20 }}>
        <div style={{ marginBottom: 10 }}>
          <label style={{ display: 'block', marginBottom: 5, fontWeight: 'bold' }}>
            Image Folder Path:
          </label>
          <input
            type="text"
            value={imageFolder}
            onChange={(e) => setImageFolder(e.target.value)}
            style={{ width: '100%', padding: 8, fontSize: 14 }}
            placeholder="./Dataset images"
          />
        </div>

        <div style={{ marginBottom: 10 }}>
          <label style={{ display: 'block', marginBottom: 5, fontWeight: 'bold' }}>
            Video Prompt:
          </label>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            style={{ width: '100%', padding: 8, fontSize: 14, minHeight: 80 }}
            placeholder="Create a wedding video with elegant transitions and warm captions..."
          />
        </div>

        <button
          onClick={handleGenerate}
          disabled={loading}
          style={{
            padding: '12px 24px',
            fontSize: 16,
            backgroundColor: loading ? '#ccc' : '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: 4,
            cursor: loading ? 'not-allowed' : 'pointer'
          }}
        >
          {loading ? 'Generating...' : 'Generate Video'}
        </button>
      </div>

      {error && (
        <div style={{ padding: 10, backgroundColor: '#f8d7da', color: '#721c24', borderRadius: 4, marginBottom: 20 }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {pipelineState && (
        <div style={{ marginBottom: 20, padding: 15, backgroundColor: '#f0f0f0', borderRadius: 4 }}>
          <h3>Pipeline State</h3>
          <p><strong>Images Found:</strong> {pipelineState.images.length}</p>
          <p><strong>Images Analyzed:</strong> {pipelineState.analysis_count}</p>
          <p><strong>Storyboard Scenes:</strong> {pipelineState.storyboard_count}</p>
          <p><strong>Retry Count:</strong> {pipelineState.retry_count}</p>
          {pipelineState.compile_error && (
            <p style={{ color: 'red' }}><strong>Compile Error:</strong> {pipelineState.compile_error}</p>
          )}
        </div>
      )}

      {storyboard.length > 0 && (
        <div style={{ marginBottom: 20 }}>
          <h2>Storyboard</h2>
          {storyboard.map((scene, index) => (
            <div
              key={index}
              style={{
                border: '1px solid #ddd',
                borderRadius: 4,
                padding: 15,
                marginBottom: 10,
                backgroundColor: '#fafafa'
              }}
            >
              <h4>Scene {scene.order}</h4>
              <p><strong>Image:</strong> {scene.image}</p>
              <p><strong>Caption:</strong> {scene.caption}</p>
              <p><strong>Duration:</strong> {scene.duration}s</p>
              <p><strong>Transition:</strong> {scene.transition}</p>
            </div>
          ))}
        </div>
      )}

      {script && (
        <div style={{ marginBottom: 20 }}>
          <h2>Generated Remotion Script</h2>
          <pre
            style={{
              backgroundColor: '#f5f5f5',
              padding: 15,
              borderRadius: 4,
              overflow: 'auto',
              fontSize: 12,
              maxHeight: 400
            }}
          >
            {script}
          </pre>
        </div>
      )}

      {videoPath && (
        <div style={{ padding: 10, backgroundColor: '#d4edda', color: '#155724', borderRadius: 4 }}>
          <strong>Video Generated:</strong> {videoPath}
        </div>
      )}
    </div>
  );
}

export default App;