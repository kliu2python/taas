import React, { useState } from 'react';

interface CommandInterfaceProps {
  onGoBack: () => void; // Callback to handle the "Go Back" button
}

const CommandInterface: React.FC<CommandInterfaceProps> = ({ onGoBack }) => {
  const [command, setCommand] = useState<string>(''); // Stores the entered command

  const executeCommand = async () => {
    if (!command.trim()) {
      alert('Please enter a command.');
      return;
    }

    try {
      const response = await fetch('http://localhost:3000/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ command }),
      });

      if (response.ok) {
        const result = await response.json();
        alert(`Command output: ${result.output || 'No output'}`);
      } else {
        alert('Failed to execute command.');
      }
    } catch (error) {
      alert(`Error: ${(error as Error).message}`);
    }
  };

  return (
    <div style={{ padding: '10px', background: '#f7f7f7', height: '100%', borderLeft: '2px solid #ccc' }}>
      <h3>Command Interface</h3>
      <input
        type="text"
        value={command}
        onChange={(e) => setCommand(e.target.value)}
        placeholder="Enter command"
        style={{ width: '100%', padding: '10px', marginBottom: '10px' }}
      />
      <div style={{ display: 'flex', gap: '10px' }}>
        {/* Enter button */}
        <button
          onClick={executeCommand}
          style={{
            padding: '10px',
            background: '#007bff',
            color: '#fff',
            border: 'none',
            cursor: 'pointer',
            flex: 1,
          }}
        >
          Enter
        </button>

        {/* Go Back button */}
        <button
          onClick={onGoBack}
          style={{
            padding: '10px',
            background: '#dc3545',
            color: '#fff',
            border: 'none',
            cursor: 'pointer',
            flex: 1,
          }}
        >
          Go Back
        </button>
      </div>
    </div>
  );
};

export default CommandInterface;
