import React, { useState, useEffect } from 'react';
import {
  BrowserRouter as Router,
  Routes,
  Route,
  useLocation,
} from 'react-router-dom';
import 'slick-carousel/slick/slick.css';
import 'slick-carousel/slick/slick-theme.css';
import 'bootstrap/dist/css/bootstrap.min.css';

import ResourcePage from './components/EmulatorCloud';
import CustomModal from './components/CustomModal';
import LoadingModal from './components/LoadingModal';
import HomePage from './components/HomePage';
import NavigateBar from './components/NavigateBar';
import ReportError from './components/ReportError';
import ResourceManagement from './components/ResourceManagement';
import Header from './components/Header';
import BrowserCloud from './components/BrowserCloud';
import config from './config/config';
import ReviewFinder from './components/ReviewFinder';
import JenkinsCloudPage from './components/JenkinsCloud';
import JobDetailPage from './components/ServerDetailPage';

interface Resource {
  adb_port: number;
  available: string;
  name: string;
  status: string;
  version: string;
  vnc_port: number;
}

const App: React.FC = () => (
  <Router>
    <AppLayout />
  </Router>
);

const AppLayout: React.FC = () => {
  const location = useLocation();
  const [nickname, setNickname] = useState<string>('');
  const [resources, setResources] = useState<Resource[]>([]);
  const [rememberNickname] = useState<boolean>(true);
  const [modalIsOpen, setModalIsOpen] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [os, setOS] = useState<string | null>(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(false);

  useEffect(() => {
    const storedNickname = localStorage.getItem('nickname');
    if (storedNickname) {
      setNickname(storedNickname);
      fetchResources(storedNickname);
    }
  }, []);

  const handleNicknameSubmit = (nickname: string) => {
    setNickname(nickname);
    if (rememberNickname) {
      localStorage.setItem('nickname', nickname);
    } else {
      localStorage.removeItem('nickname');
    }
    fetchResources(nickname);
  };

  const resetNickname = () => {
    localStorage.removeItem('nickname');
    setNickname('');
  };

  const fetchResources = async (nickname: string) => {
    setLoading(true);
    try {
      const response = await fetch(`${config.emulatorBaseUrl}/dhub/emulator/list/${nickname}`, {
        method: 'GET',
      });
      if (!response.ok) {
        throw new Error('Failed to fetch resources');
      }
      const data = await response.json();
      setResources(data.results || []);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const createEmulator = async (os: string, version: string) => {
    setLoading(true);
    try {
      const response = await fetch(`${config.emulatorBaseUrl}/dhub/emulator/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ os, version, creator: nickname }),
      });
      if (!response.ok) {
        throw new Error('Failed to create emulator');
      }
      fetchResources(nickname);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const deleteResource = async (name: string) => {
    setLoading(true);
    try {
      const response = await fetch(`${config.emulatorBaseUrl}/dhub/emulator/delete`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ pod_name: name, creator: nickname }),
      });
      if (!response.ok) {
        throw new Error('Failed to delete resource');
      }
      fetchResources(nickname);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const launchVNC = (port: number) => {
    window.open(`http://10.160.24.88:${port}/?password=fortinet`, '_blank');
  };

  const handleOSSubmit = (selectedOS: string) => {
    setOS(selectedOS);
  };

  const handleVersionSubmit = (os: string, version: string) => {
    createEmulator(os, version);
  };

  const updateResourceStatus = (name: string, status: string) => {
    setResources((prevResources) =>
      prevResources.map((resource) => (resource.name === name ? { ...resource, status } : resource))
    );
  };

  const isHomeRoute = location.pathname === '/';

  return (
    <div className={`app-shell ${sidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
      <aside className={`app-sidebar ${sidebarCollapsed ? 'collapsed' : ''}`}>
        <NavigateBar
          collapsed={sidebarCollapsed}
          onToggleSidebar={() => setSidebarCollapsed((previous) => !previous)}
        />
      </aside>
      <div className="app-main">
        <Header
          nickname={nickname}
          resetNickname={resetNickname}
          handleNicknameSubmit={handleNicknameSubmit}
          sidebarCollapsed={sidebarCollapsed}
          onToggleSidebar={() => setSidebarCollapsed((previous) => !previous)}
        />
        <main className={`app-content ${isHomeRoute ? 'is-home' : ''}`}>
          <Routes>
            <Route
              path="/"
              element={<HomePage />}
            />
            <Route
              path="/emulator-cloud"
              element={
                <ResourcePage
                  resources={resources}
                  createResource={createEmulator}
                  deleteResource={deleteResource}
                  launchVNC={launchVNC}
                  refreshPage={() => fetchResources(nickname)}
                  nickName={nickname}
                  resetNickname={resetNickname}
                  handleCreateNew={() => setModalIsOpen(true)}
                  updateResourceStatus={updateResourceStatus}
                  handleNicknameSubmit={handleNicknameSubmit}
                />
              }
            />
            <Route
              path="/browser-cloud"
              element={<BrowserCloud nickName={nickname} />}
            />
            <Route path="/jenkins-cloud" element={<JenkinsCloudPage />} />
            <Route path="/reviewfinder" element={<ReviewFinder />} />
            <Route
              path="/resource"
              element={<ResourceManagement nickName={nickname} />}
            />
            <Route
              path="/report-error"
              element={<ReportError nickName={nickname} />}
            />
            <Route path="/jenkins-cloud/:jobName" element={<JobDetailPage />} />
          </Routes>
        </main>
      </div>

      <CustomModal
        isOpen={modalIsOpen}
        onClose={() => setModalIsOpen(false)}
        onOSSubmit={handleOSSubmit}
        onVersionSubmit={handleVersionSubmit}
        os={os}
      />
      <LoadingModal isOpen={loading} />
    </div>
  );
};

export default App;
