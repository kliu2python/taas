import React from 'react';

interface BrowserCloudProps {
    nickName: string;
}

const BrowserCloud: React.FC<BrowserCloudProps> = (
    nickName
) => {
  return (
    <div style={{ padding: '20px', textAlign: 'center' }}>
      <h1>Welcome to the TaaS Cloud</h1>
      <p>Explore the Emulator Cloud and manage your resources effectively.</p>
    </div>
  );
};

export default BrowserCloud;