import React, { useState } from 'react';
import axios from 'axios';

interface Scene {
  image: string;
  caption: string;
  duration: number;
  transition: string;
  order: number;
}

interface Intent {
  pacing: string;
  style: string;
  caption_tone: string;
  transition: string;
}

interface PipelineState {
  images: string[];
  intent: Intent | null;
  analysis_count: number;
  storyboard_count: number;
  compile_error?: string;
  retry_count: number;
}

type PipelineStep = 'idle' | 'intent' | 'analyzer' | 'storyboard' | 'script' | 'compiler' | 'renderer' | 'complete';

function App() {
  const [prompt, setPrompt] = useState('');
  const [imageFolder, setImageFolder] = useState('./Dataset images');
  const [loading, setLoading] = useState(false);
  const [storyboard, setStoryboard] = useState<Scene[]>([]);
  const [script, setScript] = useState('');
  const [videoPath, setVideoPath] = useState('');
  const [pipelineState, setPipelineState] = useState<PipelineState | null>(null);
  const [error, setError] = useState('');
  const [currentStep, setCurrentStep] = useState<PipelineStep>('idle');
  const [success, setSuccess] = useState('');

  const steps: { key: PipelineStep; label: string }[] = [
    { key: 'intent', label: 'Intent Parser' },
    { key: 'analyzer', label: 'Image Analyzer' },
    { key: 'storyboard', label: 'Storyboard Writer' },
    { key: 'script', label: 'Script Generator' },
    { key: 'compiler', label: 'Compiler & Fixer' },
    { key: 'renderer', label: 'Renderer' }
  ];

  const handleGenerate = async () => {
    setLoading(true);
    setError('');
    setStoryboard([]);
    setScript('');
    setVideoPath('');
    setPipelineState(null);
    setSuccess('');
    setCurrentStep('intent');

    try {
      // Simulate progress through steps
      const stepDelays = [500, 1500, 2500, 3500, 4500, 5500];
      
      const timers: ReturnType<typeof setTimeout>[] = [];
      
      steps.forEach((step, index) => {
        const timer = setTimeout(() => {
          setCurrentStep(step.key);
        }, stepDelays[index]);
        timers.push(timer);
      });

      const response = await axios.post('http://localhost:8000/generate', {
        image_folder: imageFolder,
        user_prompt: prompt
      });

      // Clear all timers
      timers.forEach(timer => clearTimeout(timer));
      setCurrentStep('complete');
      setSuccess('Video generated successfully!');

      setStoryboard(response.data.storyboard);
      setScript(response.data.script);
      setVideoPath(response.data.video_path);
      setPipelineState(response.data.pipeline_state);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message);
      setCurrentStep('idle');
    } finally {
      setLoading(false);
    }
  };

  const getStepStatus = (stepKey: PipelineStep) => {
    if (currentStep === 'idle') return 'pending';
    if (currentStep === 'complete') return 'complete';
    
    const stepIndex = steps.findIndex(s => s.key === stepKey);
    const currentIndex = steps.findIndex(s => s.key === currentStep);
    
    if (stepIndex < currentIndex) return 'complete';
    if (stepIndex === currentIndex) return 'active';
    return 'pending';
  };

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: 20 }}>
      <h1>Image-to-Video Pipeline</h1>
      
      {/* Progress Indicator */}
      <div style={{ marginBottom: 30, padding: 20, backgroundColor: '#f8f9fa', borderRadius: 8 }}>
        <h3 style={{ marginTop: 0 }}>Pipeline Progress</h3>
        <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 10 }}>
          {steps.map((step) => {
            const status = getStepStatus(step.key);
            return (
              <div
                key={step.key}
                style={{
                  flex: '1 1 150px',
                  padding: '10px 15px',
                  borderRadius: 6,
                  textAlign: 'center',
                  fontWeight: 'bold',
                  backgroundColor: status === 'complete' ? '#d4edda' : 
                                  status === 'active' ? '#007bff' : 
                                  '#e9ecef',
                  color: status === 'complete' ? '#155724' : 
                         status === 'active' ? 'white' : 
                         '#6c757d',
                  transition: 'all 0.3s ease'
                }}
              >
                <div style={{ fontSize: 20, marginBottom: 5 }}>
                  {status === 'complete' ? '✓' : status === 'active' ? '⟳' : '○'}
                </div>
                <div style={{ fontSize: 12 }}>{step.label}</div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Intent Summary Card */}
      {pipelineState?.intent && (
        <div style={{ marginBottom: 20, padding: 15, backgroundColor: '#e7f3ff', borderRadius: 8, border: '2px solid #007bff' }}>
          <h3 style={{ marginTop: 0, color: '#007bff' }}>Video Intent</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 10 }}>
            <div><strong>Pacing:</strong> {pipelineState.intent.pacing}</div>
            <div><strong>Style:</strong> {pipelineState.intent.style}</div>
            <div><strong>Caption Tone:</strong> {pipelineState.intent.caption_tone}</div>
            <div><strong>Transition:</strong> {pipelineState.intent.transition}</div>
          </div>
        </div>
      )}

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
            cursor: loading ? 'not-allowed' : 'pointer',
            fontWeight: 'bold'
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

      {success && (
        <div style={{ padding: 15, backgroundColor: '#d4edda', color: '#155724', borderRadius: 4, marginBottom: 20, fontSize: 16, fontWeight: 'bold', textAlign: 'center' }}>
          ✓ {success}
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
              <div style={{ display: 'flex', gap: 15, alignItems: 'start' }}>
                <div style={{ flex: '0 0 200px' }}>
                  <img
                    src={`http://localhost:8000/image?path=${encodeURIComponent(scene.image)}`}
                    alt={`Scene ${scene.order}`}
                    style={{
                      width: '100%',
                      height: 150,
                      objectFit: 'cover',
                      borderRadius: 4,
                      border: '1px solid #ddd'
                    }}
                    onError={(e) => {
                      (e.target as HTMLImageElement).src = 'https://via.placeholder.com/200x150?text=Image+Not+Found';
                    }}
                  />
                </div>
                <div style={{ flex: 1 }}>
                  <p><strong>Caption:</strong> {scene.caption}</p>
                  <p><strong>Duration:</strong> {scene.duration}s</p>
                  <p><strong>Transition:</strong> {scene.transition}</p>
                </div>
              </div>
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
        <div style={{ marginBottom: 20 }}>
          <h3>Generated Video</h3>
          <video
            controls
            style={{
              width: '100%',
              maxWidth: 800,
              borderRadius: 8,
              border: '2px solid #007bff'
            }}
          >
            <source src={`http://localhost:8000/video?path=${encodeURIComponent(videoPath)}`} type="video/mp4" />
            Your browser does not support the video tag.
          </video>
          <p style={{ marginTop: 10, color: '#666' }}>
            <strong>Path:</strong> {videoPath}
          </p>
        </div>
      )}
    </div>
  );
}

export default App;