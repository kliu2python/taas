import React from 'react';
import { 
  Modal,
  Button,
  Table,
  Spinner
} from 'react-bootstrap';

interface TestResult {
  name: string;
  res: string;
  build_url: string;
  platform: string;
  started_at?: string;
  updated_at?: string; // ISO string or formatted string
}

interface TestResultsModalProps {
  show: boolean;
  onClose: () => void;
  testResultLogs: TestResult[];
  onRefreshAll: () => void;
  onRefreshSingle: (jobName: string, index: number) => void;
  refreshingIndex: number | null;
  fullscreen?: boolean; // Optional: default to true;
  deleteSingleResult: (jobName: string, index: number) => void;
}

const TestResultsModal: React.FC<TestResultsModalProps> = ({
  show,
  onClose,
  testResultLogs,
  onRefreshAll,
  onRefreshSingle,
  refreshingIndex,
  fullscreen = true,
  deleteSingleResult
}) => {
  return (
    <Modal
        show={show}
        onHide={onClose}
        fullscreen={fullscreen ? true : undefined}
        scrollable
        >
      <Modal.Header closeButton>
        <Modal.Title>Test Results</Modal.Title>
      </Modal.Header>
      <Modal.Body style={{ padding: '1.5rem' }}>
        <div className="d-flex justify-content-between align-items-center mb-3">
          <h5 className="mb-0">Test Results</h5>
          <Button size="sm" onClick={onRefreshAll}>Refresh All</Button>
        </div>
        {
          testResultLogs.length === 0 ? (
            <div className="text-center text-muted py-4">
              There are no test results.
            </div>
          ) : (
            <Table striped bordered hover size="sm">
              <thead>
                <tr>
                  <th>Build URL</th>
                  <th>Allure Result</th>
                  <th>Status</th>
                  <th>Platform</th>
                  <th>Started At</th>
                  <th>Updated At</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {Array.isArray(testResultLogs) && testResultLogs.length > 0 ? (
                  testResultLogs.map((log, idx) => {
                    const url = log.build_url || '';
                    const allureUrl = url ? `${url.replace(/\/$/, '')}/allure` : '';
                    const jobName = `${log.name}`.replace(/[^a-zA-Z0-9]/g, '');

                    return (
                      <tr key={idx}>
                        <td><a href={url} target="_blank" rel="noreferrer">Build URL</a></td>
                        <td>{log.res === 'running'
                          ? 'Unavailable'
                          : <a href={allureUrl} target="_blank" rel="noreferrer">Allure</a>}</td>
                        <td>{log.res || 'Unknown'}</td>
                        <td>{log.platform}</td>
                        <td>{log.started_at ? new Date(log.started_at).toLocaleString() : 'N/A'}</td>
                        <td>{log.updated_at ? new Date(log.updated_at).toLocaleString() : 'N/A'}</td>
                        <td>
                          {log.res === 'running' ? (
                            <Button
                              size="sm"
                              disabled={refreshingIndex === idx}
                              onClick={() => onRefreshSingle(jobName, idx)}
                            >
                              {refreshingIndex === idx ? <Spinner animation="border" size="sm" /> : 'Refresh'}
                            </Button>
                          ) : (
                            <Button
                              size="sm"
                              disabled={refreshingIndex === idx}
                              onClick={() => deleteSingleResult(jobName, idx)}
                            >
                              {refreshingIndex === idx ? <Spinner animation="border" size="sm" /> : 'Delete'}
                            </Button>
                          )}
                        </td>
                      </tr>
                    );
                  })
                ) : (
                  <tr>
                    <td colSpan={7} className="text-center text-muted">There are no test results.</td>
                  </tr>
                )}
          </tbody>
        </Table>
      )}
      </Modal.Body>

      <Modal.Footer>
        <Button variant="secondary" onClick={onClose}>
          Close
        </Button>
      </Modal.Footer>
    </Modal>
  );
};

export default TestResultsModal;
