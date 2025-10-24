import React from 'react';
import { Link } from 'react-router-dom';
import { IconType } from 'react-icons';
import {
  FiActivity,
  FiAlertTriangle,
  FiCloud,
  FiCommand,
  FiSearch,
  FiSmartphone,
} from 'react-icons/fi';

interface HomePageProps {
  nickName?: string;
}

interface FeatureCard {
  title: string;
  description: string;
  to: string;
  icon: IconType;
  accent: string;
}

const features: FeatureCard[] = [
  {
    title: 'Launch Emulator Labs',
    description: 'Spin up Android or iOS devices instantly and manage them in one view.',
    to: '/emulator-cloud',
    icon: FiSmartphone,
    accent: 'accent-blue',
  },
  {
    title: 'Explore Browser Cloud',
    description: 'Open disposable browser sessions tailored to every testing workflow.',
    to: '/browser-cloud',
    icon: FiCommand,
    accent: 'accent-teal',
  },
  {
    title: 'Monitor Jenkins Pipelines',
    description: 'Track job health and restart builds without leaving the dashboard.',
    to: '/jenkins-cloud',
    icon: FiCloud,
    accent: 'accent-purple',
  },
  {
    title: 'Review Customer Feedback',
    description: 'Surface Fortinet review trends to guide release priorities.',
    to: '/reviewfinder',
    icon: FiSearch,
    accent: 'accent-orange',
  },
  {
    title: 'Manage Shared Resources',
    description: 'Watch utilization, reservations, and capacity in real time.',
    to: '/resource',
    icon: FiActivity,
    accent: 'accent-cyan',
  },
  {
    title: 'Report an Issue',
    description: 'Alert the TaaS team about outages or urgent incidents with context.',
    to: '/report-error',
    icon: FiAlertTriangle,
    accent: 'accent-rose',
  },
];

const HomePage: React.FC<HomePageProps> = ({ nickName }) => {
  const userName = nickName || 'Guest';

  return (
    <div className="home-page">
      <section className="home-hero">
        <span className="home-hero-badge">Test as a Service</span>
        <h1>
          Welcome back, <span>{userName}</span>
        </h1>
        <p>
          Launch devices, browsers, CI insights, and resource intelligence without hopping between tools.
        </p>
        <div className="home-hero-actions">
          <Link to="/emulator-cloud" className="cta-primary">
            Go to Emulator Cloud
          </Link>
          <Link to="/report-error" className="cta-secondary">
            Report an Issue
          </Link>
        </div>
      </section>

      <section className="home-feature-grid" aria-label="Available services">
        {features.map(({ title, description, to, icon, accent }) => {
          const iconElement = React.createElement(icon as React.ComponentType);
          return (
            <Link key={title} to={to} className={`home-feature-card ${accent}`}>
              <span className="home-feature-icon">{iconElement}</span>
              <div className="home-feature-content">
                <h3>{title}</h3>
                <p>{description}</p>
              </div>
            </Link>
          );
        })}
      </section>

      <section className="home-info-panel">
        <h2>Getting started is simple</h2>
        <div className="home-info-grid">
          <article className="home-info-step">
            <span>1</span>
            <h3>Authenticate instantly</h3>
            <p>Enter your assigned nickname to unlock emulator, browser, and reporting tools.</p>
          </article>
          <article className="home-info-step">
            <span>2</span>
            <h3>Choose your workspace</h3>
            <p>Jump into the service you need—from mobile labs to Jenkins job tracking—in one click.</p>
          </article>
          <article className="home-info-step">
            <span>3</span>
            <h3>Collaborate and iterate</h3>
            <p>Share insights, flag issues, and coordinate releases with the wider QA team.</p>
          </article>
        </div>
      </section>
    </div>
  );
};

export default HomePage;
