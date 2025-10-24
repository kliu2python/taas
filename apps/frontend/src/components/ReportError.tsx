import React, { useState } from 'react';


interface ReportErrorProps {
    nickName: string;
}

const ReportError: React.FC<ReportErrorProps> = ({
    nickName
}) => {
  const [errorTitle, setErrorTitle] = useState<string>('');
  const [errorContent, setErrorContent] = useState<string>('');
  const [category, setCategory] = useState<string>('Emulator Cloud');
  const [successMessage, setSuccessMessage] = useState<string>('');
  const [errorMessage, setErrorMessage] = useState<string>('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSuccessMessage('');
    setErrorMessage('');

    if (!errorTitle || !errorContent || !category) {
      setErrorMessage('Please fill in all fields.');
      return;
    }

    try {
      const response = await fetch('http://10.160.83.213:8309/send-error-report', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: errorTitle,
          content: errorContent,
          category,
          recipient: 'ljiahao@fortinet.com',
        }),
      });

      if (response.ok) {
        setSuccessMessage('Error report sent successfully!');
        setErrorTitle('');
        setErrorContent('');
        setCategory('Emulator Cloud');
      } else {
        throw new Error('Failed to send error report');
      }
    } catch (error) {
      setErrorMessage('An error occurred while sending the report. Please try again later.');
      console.error(error);
    }
  };

  return (
    <div className="container mt-4">
      <h3 className="text-center mb-4">Report an Issue</h3>
      <form onSubmit={handleSubmit}>
        {/* Error Title */}
        <div className="mb-3">
          <label htmlFor="errorTitle" className="form-label">
            Error Title
          </label>
          <input
            type="text"
            className="form-control"
            id="errorTitle"
            value={errorTitle}
            onChange={(e) => setErrorTitle(e.target.value)}
            placeholder="Enter a brief error title"
            required
          />
        </div>

        {/* Category Dropdown */}
        <div className="mb-3">
          <label htmlFor="category" className="form-label">
            Category
          </label>
          <select
            className="form-select"
            id="category"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            required
          >
            <option value="Emulator Cloud">Emulator Cloud</option>
            <option value="Browser Cloud">Browser Cloud</option>
            <option value="Benchmark Automation">Benchmark Automation</option>
            <option value="Infrastructure">Infrastructure</option>
          </select>
        </div>

        {/* Error Description */}
        <div className="mb-3">
          <label htmlFor="errorContent" className="form-label">
            Error Description
          </label>
          <textarea
            className="form-control"
            id="errorContent"
            value={errorContent}
            onChange={(e) => setErrorContent(e.target.value)}
            placeholder="Describe the issue in detail"
            rows={5}
            required
          ></textarea>
        </div>

        {/* Submit Button */}
        <button type="submit" className="btn btn-primary w-100" disabled={!nickName}>
          Submit Report
        </button>

        {/* Success or Error Message */}
        {successMessage && (
          <div className="alert alert-success mt-3" role="alert">
            {successMessage}
          </div>
        )}
        {errorMessage && (
          <div className="alert alert-danger mt-3" role="alert">
            {errorMessage}
          </div>
        )}
      </form>
    </div>
  );
};

export default ReportError;
