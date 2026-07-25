import React from 'react';
import { Composition } from 'remotion';
import { Video } from './Video';

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="Video"
        component={Video}
        durationInFrames={150}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          scenes: []
        }}
      />
    </>
  );
};