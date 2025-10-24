import React from 'react';
import { useLocation } from 'react-router-dom';
import { Dropdown } from 'react-bootstrap';
import NickNamePage from './nickname';

import { unslugify } from '../utils/slugify';

interface HeaderProps {
  nickname: string;
  resetNickname: () => void;
  handleNicknameSubmit: (nickname: string) => void;
}

const Header: React.FC<HeaderProps> = ({ nickname, resetNickname, handleNicknameSubmit }) => {
  const location = useLocation();

  const getTitle = (path: string): string => {
    if (path.startsWith('/jenkins-cloud/')) {
      // Extract server slug after "/jenkins-cloud/"
      const serverSlug = path.replace('/jenkins-cloud/', '');
      if (serverSlug) {
        return unslugify(serverSlug);
      }
      return 'Jenkins Cloud';
    }
    
    switch (path) {
        case '/emulator-cloud':
            return 'Emulator Resources';
        case '/browser-cloud':
            return 'Browser Resources';
        case '/reviewfinder':
            return 'FTNT Review Finder';
        case '/jenkins-cloud':
          return 'Jenkins Cloud';
        case '/resource':
            return 'Resource Dashboard';
        case '/report-error':
            return 'Report an Error';
        case '/':
            return 'Home';
        default:
            return 'TaaS Cloud';
    }
  };

  const title = getTitle(location.pathname);

  const descriptions: Record<string, string> = {
    '/': 'Navigate faster with curated entry points into every quality engineering surface.',
    '/emulator-cloud': 'Launch, monitor, and recycle on-demand mobile device labs across platforms.',
    '/browser-cloud': 'Provision isolated browser sessions in seconds for compatibility testing.',
    '/reviewfinder': 'Research authentic customer sentiment with curated Fortinet feedback streams.',
    '/jenkins-cloud': 'Track multi-project CI pipelines and drill into job-level diagnostics.',
    '/resource': 'Review lab capacity, utilization trends, and reservation health at a glance.',
    '/report-error': 'Flag issues for the TaaS crew with context-rich, actionable reports.',
  };

  const getDescription = (path: string): string => {
    if (path.startsWith('/jenkins-cloud/')) {
      return 'Inspect build telemetry and artifact history for targeted Jenkins jobs.';
    }

    return descriptions[path] || 'A modern workspace designed to orchestrate every test workflow in one place.';
  };

  const loginEnabledPaths = ['/emulator-cloud', '/browser-cloud', '/report-error'];
  // Check if the path is one of the specific ones where nickname and login should be shown
  const showLogin = loginEnabledPaths.some((path) => location.pathname.startsWith(path));

  const description = getDescription(location.pathname);

  return (
    <header className="page-header">
      <div className="page-title-group">
        <span className="page-eyebrow">Fortinet TaaS</span>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {showLogin && (
        <div className="page-header-actions">
          {nickname ? (
            <Dropdown align="end">
              <Dropdown.Toggle variant="light" className="header-profile">
                <span className="header-profile-initials">{nickname.slice(0, 2).toUpperCase()}</span>
                <span className="header-profile-name">{nickname}</span>
              </Dropdown.Toggle>
              <Dropdown.Menu className="header-profile-menu">
                <Dropdown.Item onClick={resetNickname}>Logout</Dropdown.Item>
              </Dropdown.Menu>
            </Dropdown>
          ) : (
            <NickNamePage onSubmit={handleNicknameSubmit} />
          )}
        </div>
      )}
    </header>
  );
};

export default Header;
