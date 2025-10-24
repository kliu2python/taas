import React from 'react';
import { Link } from 'react-router-dom';

const NavigateBar: React.FC = () => {
  return (
    <div
      className="bg-dark text-white d-flex flex-column justify-content-between p-3"
      style={{ width: '250px', minHeight: '100vh' }}
    >
      {/* Header */}
      <div>
        <div className="text-center mb-4">
          <h3 className="mb-1">TaaS</h3>
          <h6 className="mb-1">Test as a Service</h6>
        </div>
        <Link to="/" className="btn btn-outline-light d-block mb-3">
          Home
        </Link>
        <Link to="/emulator-cloud" className="btn btn-outline-light d-block mb-3">
          Emulator Cloud
        </Link>
        <Link to="/browser-cloud" className="btn btn-outline-light d-block mb-3">
          Browser Cloud
        </Link>
        <Link to="/jenkins-cloud" className="btn btn-outline-light d-block mb-3">
          Jenkins Cloud
        </Link>
        <Link to="/reviewfinder" className="btn btn-outline-light d-block mb-3">
          FortiReviewFinder
        </Link>
        <Link to="/resource" className="btn btn-outline-light d-block mb-3">
          Resource Dashboard
        </Link>
        <Link to="/report-error" className="btn btn-outline-light d-block mb-3">
          Report an Issue
        </Link>
      </div>

      {/* Footer */}
      <div className="text-center mt-4">
        <hr className="border-light" />
        <p className="mb-1">Version: 6.0.0</p>
        <p className="mb-0">Editor: Jiahao Liu (ljiahao@fortinet.com)</p>
      </div>
    </div>
  );
};

export default NavigateBar;
