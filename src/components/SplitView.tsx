import React, { useState } from 'react';

import { Resource } from './EmulatorCloud';
import config from '../config/config';

interface SplitViewProps {
  resource: Resource;
  launchVNC: (port: number) => void;
  onGoBack: () => void;
}

interface Emulator {
  name: string;
  pid: string;
}

const SplitView: React.FC<SplitViewProps> = ({ resource, launchVNC, onGoBack }) => {
  const [command, setCommand] = useState('');
  const [dns, setDns] = useState('');
  const [emulatorName, setEmulatorName] = useState('google_api');
  const [apkFile, setApkFile] = useState('fortitoken-dev-20241203.apk');
  const [message, setMessage] = useState<string | null>(null);
  const [launchedEmulators, setLaunchedEmulators] = useState<Emulator[]>([]);
  const [selectedEmulator, setSelectedEmulator] = useState<string>('');

  const handleCommandSubmit = async (cmd: string) => {
    if (!cmd.trim()) {
      setMessage('Command cannot be empty.');
      return;
    }

    try {
      const response = await fetch(`${config.emulatorBaseUrl}/dhub/emulator/adb/${resource.name}/${encodeURIComponent(cmd)}`, {
        method: 'POST',
      });

      if (response.ok) {
        if (cmd === '4') {
          cmd = 'back to previous';
        }
        setMessage(`Command "${cmd}" executed successfully!`);
      } else {
        setMessage(`Failed to execute the command "${cmd}".`);
      }
    } catch (error) {
      console.error('Error sending command:', error);
      setMessage('An error occurred while sending the command.');
    } finally {
      if (cmd !== 'back') {
        setCommand(''); // Clear input field for normal commands
      }
    }
  };

  const handleLaunchEmulator = async () => {
    const requestBody: { pod_name: string; emulator_name: string; dns?: string } = {
        pod_name: resource.name,
        emulator_name: emulatorName,
      };
    
    // Include dns in the body only if it's not empty
    if (dns.trim()) {
        requestBody.dns = dns;
    }

    try {
      const response = await fetch(`${config.emulatorBaseUrl}/dhub/emulator/launch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
      });

      if (response.ok) {
        const data = await response.json();
        const pid = data.pid;
        setLaunchedEmulators((prev) => [...prev, { name: emulatorName, pid }]);
        setMessage('Emulator launched successfully!');
      } else {
        setMessage('Failed to launch emulator.');
      }
    } catch (error) {
      console.error('Error launching emulator:', error);
      setMessage('An error occurred while launching the emulator.');
    }
  };

  const handleOpenTerminal = async () => {
    const emulator = launchedEmulators.find((e) => e.name === selectedEmulator);
    if (!emulator) {
      setMessage('Please select a valid emulator.');
      return;
    }

    console.log(emulator)
    try {
      const response = await fetch(
        `${config.emulatorBaseUrl}/dhub/emulator/terminal/${resource.name}/${emulator.pid}`,
        { method: 'POST' }
      );

      if (response.ok) {
        setMessage(`Terminal opened for emulator "${selectedEmulator}".`);
        setLaunchedEmulators((prev) => prev.filter((e) => e.name !== selectedEmulator)); // Remove from list
        setSelectedEmulator('');
      } else {
        setMessage('Failed to open terminal.');
      }
    } catch (error) {
      console.error('Error opening terminal:', error);
      setMessage('An error occurred while opening the terminal.');
    }
  };

  return (
    <div style={{ display: 'flex', height: '89vh' }}>
      {/* VNC View */}
      <div style={{ flex: 1, padding: '10px' }}>
        <iframe
          src={`http://10.160.24.88:${resource.vnc_port}/?password=fortinet`}
          width="100%"
          height="100%"
          style={{ border: 'none' }}
        ></iframe>
      </div>

      {/* Command Interface */}
      <div
        style={{
          width: '300px',
          padding: '10px',
          background: '#f7f7f7',
          borderLeft: '2px solid #ccc',
          display: 'flex',
          flexDirection: 'column',
          gap: '20px',
        }}
      >
        {/* Exit Block */}
        <div>
          <button onClick={onGoBack} style={{ padding: '5px', width: '100%' }}>
            Exit
          </button>
        </div>

        {/* Launch Emulator Block */}
        <div>
          <h4>Launch Emulator</h4>
          <label htmlFor="dns-input" style={{ marginBottom: '5px', fontWeight: 'bold' }}>
            DNS:
          </label>
          <input
            id="dns-input"
            type="text"
            value={dns}
            onChange={(e) => setDns(e.target.value)}
            style={{ marginBottom: '10px', padding: '5px', width: '100%' }}
            placeholder='Leavt it empty if do not want'
          />

          <label htmlFor="emulator-select" style={{ marginBottom: '5px', fontWeight: 'bold' }}>
            Emulator Name:
          </label>
          <select
            id="emulator-select"
            value={emulatorName}
            onChange={(e) => setEmulatorName(e.target.value)}
            style={{ marginBottom: '10px', padding: '5px', width: '100%' }}
          >
            <option value="google_api">Google API</option>
            <option value="android_api">Android API</option>
          </select>

          <label htmlFor="apk-select" style={{ marginBottom: '5px', fontWeight: 'bold' }}>
            APK File:
          </label>
          <select
            id="apk-select"
            value={apkFile}
            onChange={(e) => setApkFile(e.target.value)}
            style={{ marginBottom: '10px', padding: '5px', width: '100%' }}
          >
            <option value="fortitoken-dev-20241203.apk">fortitoken-dev-20241203.apk</option>
            <option value="fortitoken-dev-20241206.apk">fortitoken-dev-20241206.apk</option>
          </select>

          <button onClick={handleLaunchEmulator} style={{ padding: '5px', width: '100%' }}>
            Launch
          </button>

          <label htmlFor="launched-emulators" style={{ marginTop: '10px', fontWeight: 'bold' }}>
            Launched Emulators:
          </label>
          <select
            id="launched-emulators"
            value={selectedEmulator}
            onChange={(e) => setSelectedEmulator(e.target.value)}
            style={{ marginBottom: '10px', padding: '5px', width: '100%' }}
          >
            <option value="">-- Select Emulator --</option>
            {launchedEmulators.map((emulator) => (
              <option key={emulator.pid} value={emulator.name}>
                {emulator.name}
              </option>
            ))}
          </select>

          <button onClick={handleOpenTerminal} style={{ padding: '5px', width: '100%' }}>
            Terminal
          </button>
        </div>

        {/* ADB Command Line Block */}
        <div>
          <h4>ADB Command Line</h4>
          <label htmlFor="command-input" style={{ marginBottom: '5px', fontWeight: 'bold' }}>
            Enter Command:
          </label>
          <input
            id="command-input"
            type="text"
            value={command}
            onChange={(e) => setCommand(e.target.value)}
            style={{ marginBottom: '10px', padding: '5px', width: '100%' }}
          />

          <button onClick={() => handleCommandSubmit(command)} style={{ marginBottom: '10px', padding: '5px', width: '100%' }}>
            Enter
          </button>
          <button onClick={() => handleCommandSubmit('4')} style={{ padding: '5px', width: '100%' }}>
            Back
          </button>
        </div>

        {message && (
          <div
            style={{
              marginTop: '10px',
              padding: '10px',
              backgroundColor: '#e7f3fe',
              border: '1px solid #b3d4fc',
              borderRadius: '5px',
              color: '#3178c6',
            }}
          >
            {message}
          </div>
        )}
      </div>
    </div>
  );
};

export default SplitView;
