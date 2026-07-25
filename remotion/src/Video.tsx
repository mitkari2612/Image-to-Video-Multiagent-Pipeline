import React from 'react';
import {
  Sequence,
  Img,
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
  useVideoConfig
} from 'remotion';

interface Scene {
  image: string;
  caption: string;
  duration: number;
  transition: string;
  order: number;
}

interface VideoProps {
  scenes: Scene[];
}

export const Video: React.FC<VideoProps> = ({ scenes }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  
  let currentFrame = 0;
  
  return (
    <AbsoluteFill>
      {scenes.map((scene, index) => {
        const durationInFrames = scene.duration * fps;
        const sequenceFrom = currentFrame;
        currentFrame += durationInFrames;
        
        return (
          <Sequence
            key={index}
            from={sequenceFrom}
            durationInFrames={durationInFrames}
          >
            <AbsoluteFill>
              <Img
                src={scene.image}
                style={{
                  width: '100%',
                  height: '100%',
                  objectFit: 'cover'
                }}
              />
              <div
                style={{
                  position: 'absolute',
                  bottom: 50,
                  left: 50,
                  color: 'white',
                  fontSize: 32,
                  fontFamily: 'Arial, sans-serif',
                  backgroundColor: 'rgba(0, 0, 0, 0.6)',
                  padding: '15px 25px',
                  borderRadius: 8,
                  maxWidth: '80%'
                }}
              >
                {scene.caption}
              </div>
            </AbsoluteFill>
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};

export default Video;