import React from 'react';

interface VNCViewerProps {
  port: number;
}

const VNCViewer: React.FC<VNCViewerProps> = ({ port }) => {
  return (
    <iframe
      src={`http://10.160.24.88:${port}/?password=fortinet`}
      style={{ flex: 2, border: 'none', height: '100%' }}
      title={`VNC Viewer on Port ${port}`}
    ></iframe>
  );
};

export default VNCViewer;
