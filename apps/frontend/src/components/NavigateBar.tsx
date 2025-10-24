import React from 'react';
import { NavLink } from 'react-router-dom';
import { IconType } from 'react-icons';
import {
  FiAlertCircle,
  FiBarChart2,
  FiChevronLeft,
  FiChevronRight,
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

interface NavigateBarProps {
  collapsed: boolean;
  onToggleSidebar: () => void;
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

const NavigateBar: React.FC<NavigateBarProps> = ({ collapsed, onToggleSidebar }) => {
  const ToggleGlyph = (collapsed ? FiChevronRight : FiChevronLeft) as React.ElementType;
  return (
    <nav className={`navigation-panel ${collapsed ? 'is-collapsed' : ''}`}>
      <div className="navigation-brand">
        <button
          type="button"
          className="navigation-toggle"
          onClick={onToggleSidebar}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {React.createElement(ToggleGlyph)}
        </button>
        {!collapsed && (
          <>
            <span className="navigation-badge">TaaS Portal</span>
            <h2>Test as a Service</h2>
            <p>Your launchpad for quality engineering tools.</p>
          </>
        )}
        {collapsed && <span className="navigation-badge">TaaS</span>}
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
                  collapsed ? 'collapsed' : '',
                  isActive ? 'active' : '',
                ]
                  .filter(Boolean)
                  .join(' ')
              }
            >
              <span className="navigation-icon">{iconElement}</span>
              {!collapsed && (
                <span className="navigation-copy">
                  <strong>{label}</strong>
                  <small>{description}</small>
                </span>
              )}
              {collapsed && <span className="sr-only">{label}</span>}
            </NavLink>
          );
        })}
      </div>

      {!collapsed && (
        <div className="navigation-footer">
          <p>Version 6.0.0</p>
          <p>Maintained by Jiahao Liu</p>
          <a href="mailto:ljiahao@fortinet.com">ljiahao@fortinet.com</a>
        </div>
      )}
    </nav>
  );
};

export default NavigateBar;
