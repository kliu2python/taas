import React from 'react';
import { NavLink } from 'react-router-dom';
import { IconType } from 'react-icons';
import {
  FiAlertCircle,
  FiBarChart2,
  FiCloud,
  FiCommand,
  FiHome,
  FiSearch,
  FiSmartphone,
} from 'react-icons/fi';

interface NavItem {
  to: string;
  label: string;
  description: string;
  icon: IconType;
  accent: string;
}

const navItems: NavItem[] = [
  {
    to: '/',
    label: 'Home',
    description: 'Overview & quick actions',
    icon: FiHome,
    accent: 'accent-indigo',
  },
  {
    to: '/emulator-cloud',
    label: 'Emulator Cloud',
    description: 'Provision Android & iOS devices',
    icon: FiSmartphone,
    accent: 'accent-blue',
  },
  {
    to: '/browser-cloud',
    label: 'Browser Cloud',
    description: 'Spin up disposable browser labs',
    icon: FiCommand,
    accent: 'accent-teal',
  },
  {
    to: '/jenkins-cloud',
    label: 'Jenkins Cloud',
    description: 'Monitor CI pipelines & jobs',
    icon: FiCloud,
    accent: 'accent-purple',
  },
  {
    to: '/reviewfinder',
    label: 'FortiReviewFinder',
    description: 'Curated customer feedback',
    icon: FiSearch,
    accent: 'accent-orange',
  },
  {
    to: '/resource',
    label: 'Resource Dashboard',
    description: 'Utilization & reservation insights',
    icon: FiBarChart2,
    accent: 'accent-cyan',
  },
  {
    to: '/report-error',
    label: 'Report an Issue',
    description: 'Notify the team about problems',
    icon: FiAlertCircle,
    accent: 'accent-rose',
  },
];

const NavigateBar: React.FC = () => {
  return (
    <nav className="navigation-panel">
      <div className="navigation-brand">
        <span className="navigation-badge">TaaS Portal</span>
        <h2>Test as a Service</h2>
        <p>Your launchpad for quality engineering tools.</p>
      </div>

      <div className="navigation-links">
        {navItems.map(({ to, label, description, icon, accent }) => {
          const iconElement = React.createElement(icon as React.ComponentType);
          return (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                [
                  'navigation-link',
                  accent,
                  isActive ? 'active' : '',
                ]
                  .filter(Boolean)
                  .join(' ')
              }
            >
              <span className="navigation-icon">{iconElement}</span>
              <span className="navigation-copy">
                <strong>{label}</strong>
                <small>{description}</small>
              </span>
            </NavLink>
          );
        })}
      </div>

      <div className="navigation-footer">
        <p>Version 6.0.0</p>
        <p>Maintained by Jiahao Liu</p>
        <a href="mailto:ljiahao@fortinet.com">ljiahao@fortinet.com</a>
      </div>
    </nav>
  );
};

export default NavigateBar;
