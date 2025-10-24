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
  nickName?: string; // Made it optional to handle cases where it might not be passed
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
    description: 'Request Android or iOS devices on demand and manage them with fine-grained controls.',
    to: '/emulator-cloud',
    icon: FiSmartphone,
    accent: 'accent-blue',
  },
  {
    title: 'Explore Browser Cloud',
    description: 'Spawn isolated browser environments for exploratory, regression, and compatibility testing.',
    to: '/browser-cloud',
    icon: FiCommand,
    accent: 'accent-teal',
  },
  {
    title: 'Monitor Jenkins Pipelines',
    description: 'Stay on top of build health, investigate failures, and relaunch jobs when needed.',
    to: '/jenkins-cloud',
    icon: FiCloud,
    accent: 'accent-purple',
  },
  {
    title: 'Review Customer Feedback',
    description: 'Surface trends from Fortinet reviews to inform release readiness and prioritization.',
    to: '/reviewfinder',
    icon: FiSearch,
    accent: 'accent-orange',
  },
  {
    title: 'Manage Shared Resources',
    description: 'Track capacity, reservations, and utilization metrics across shared lab assets.',
    to: '/resource',
    icon: FiActivity,
    accent: 'accent-cyan',
  },
  {
    title: 'Report an Issue',
    description: 'Quickly alert the TaaS team about outages, anomalies, or urgent needs.',
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
          Power every stage of your validation workflow with a unified dashboard that brings emulators,
          browsers, CI pipelines, and resource management together.
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
              <span className="home-feature-icon">
                {iconElement}
              </span>
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
            <p>Use your assigned nickname in the header to unlock emulator, browser, and reporting tools.</p>
          </article>
          <article className="home-info-step">
            <span>2</span>
            <h3>Choose your workspace</h3>
            <p>Launch the service you need, from mobile labs to Jenkins job tracking, with a single click.</p>
          </article>
          <article className="home-info-step">
            <span>3</span>
            <h3>Collaborate and iterate</h3>
            <p>Share insights, flag issues, and optimize usage with dashboards built for modern QA teams.</p>
          </article>
        </div>
      </section>
    </div>
  );
};

export default HomePage;
