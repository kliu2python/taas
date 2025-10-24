import React, { useEffect, useState } from 'react';
import { useLocation, useParams, useNavigate } from 'react-router-dom';
import { Container, Form, Button, Spinner, Alert, Toast, ToastContainer} from 'react-bootstrap';

import config from '../config/config'

const JobDetailPage: React.FC = () => {
  const { jobName } = useParams();
  const navigate = useNavigate();
  const { state } = useLocation();
  const server = state?.server;
  const [jobExists, setJobExists] = useState<boolean | null>(null);
  const [params, setParams] = useState<any[]>([]);
  const [inputValues, setInputValues] = useState<{ [key: string]: string }>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRunDoc, setAutoRunDoc] = useState<any | null>(null);
  const [buildStatuses, setBuildStatuses] = useState<{ [key: number]: string }>({});
  const [showSuccessToast, setShowSuccessToast] = useState(false);

  useEffect(() => {
    if (!server || !jobName) return;

    const checkJob = async () => {
      try {
        const res = await fetch(`${config.jenkinsCloudUrl}/api/v1/jenkins_cloud/jobs/${jobName}`);
        const data = await res.json();
        if (Object.keys(data).length > 0) {
          
            console.log("hello");
          if (data.documents.length > 0) {
            const doc = data.documents[0];
            if (doc.builds && Object.keys(doc.builds).length > 0) {
              setAutoRunDoc(doc);
              Object.entries(doc.builds).forEach(([key, build]: [string, any]) => {
                setBuildStatuses(prev => ({ ...prev, [build.build_num]: 'Loading...' }));
                refreshBuildStatus(build.build_num);
              });
              setLoading(false);
              return;
            }

            const parameters = doc.parameters || [];
            setJobExists(true);
            setParams(parameters);
            setInputValues({
              job_name: jobName,
              server_ip: doc.server_ip,
              server_un: doc.server_un,
              server_pw: doc.server_pw,
              ...Object.fromEntries(parameters.map((p: any) => [p.name, p.default || '']))
            });
          } else {
            setJobExists(false);
          }
        }
      } catch (err) {
        setError('Failed to fetch job data');
      } finally {
        setLoading(false);
      }
    };

    checkJob();
  }, [jobName, server]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setInputValues(prev => ({ ...prev, [name]: value }));
  };

  const handleRun = async () => {
    let body;

    if (autoRunDoc) {
      body = JSON.stringify(autoRunDoc);
    } else {
      const { job_name, server_ip, server_un, server_pw, ...restParams } = inputValues;
      body = JSON.stringify({
        job_name,
        server_ip,
        server_un,
        server_pw,
        parameters: restParams
      });
    }

    const res = await fetch(`${config.jenkinsCloudUrl}/api/v1/jenkins_cloud/execute/job`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body,
    });

    if (res.ok) {
      setShowSuccessToast(true);
      setTimeout(() => window.location.reload(), 2000); // wait for toast to show
    } else {
      alert('Failed to start job');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'SUCCESS': return 'green';
      case 'FAILURE': return 'red';
      case 'ABORTED': return 'orange';
      case 'Loading...': return 'gray';
      default: return 'gray';
    }
  };

  const refreshBuildStatus = async (build_num: number) => {
    setBuildStatuses(prev => ({ ...prev, [build_num]: 'Loading...' }));
    try {
      const res = await fetch(`${config.jenkinsCloudUrl}/api/v1/jenkins_cloud/jobs/build/result?job_name=${jobName}&build_number=${build_num}`);
      const data = await res.json();
      if (data && data) {
        setBuildStatuses(prev => ({ ...prev, [build_num]: data }));
      } else {
        setBuildStatuses(prev => ({ ...prev, [build_num]: 'Unknown' }));
      }
    } catch (err) {
      console.error('Failed to refresh build status', err);
      setBuildStatuses(prev => ({ ...prev, [build_num]: 'Error' }));
    }
  };

  useEffect(() => {
    const interval = setInterval(() => {
      if (autoRunDoc?.builds && Object.keys(autoRunDoc.builds).length > 0) {
        Object.entries(autoRunDoc.builds).forEach(([key, build]: [string, any]) => {
          const buildNum = build.build_num;
          if (buildStatuses[buildNum] === 'Loading...') {
            refreshBuildStatus(buildNum);
          }
        });
      }
  }, 300000); // 5 minutes

    return () => clearInterval(interval);
  }, [autoRunDoc]);

  if (loading) return <Spinner animation="border" />;

  if (error) return <Alert variant="danger">{error}</Alert>;

  return (
    <Container className="mt-4">
    <div className="d-flex justify-content-between align-items-center mb-3">
      <Button variant="secondary" onClick={() => navigate('/jenkins-cloud')}>&larr; Exit</Button>
    </div>

    {jobExists ? (
      <>
        <Form>
          {params.map((param, idx) => (
            <Form.Group key={idx} className="mb-3">
              <Form.Label>{param.name}</Form.Label>
              <Form.Control
                name={param.name}
                placeholder={param.description || ''}
                defaultValue={param.default}
                onChange={handleChange}
              />
            </Form.Group>
          ))}
        </Form>
        <Button onClick={handleRun}>Run</Button>
      </>
    ) : autoRunDoc ? (
      <>
        <h5>Previous Builds</h5>
        <ul>
          {Object.entries(autoRunDoc.builds).map(([key, build]: [string, any], idx: number) => {
            const allureUrl = `${build.build_url.replace(/\/$/, '')}/allure`;
            const rawStatus = buildStatuses[build.build_num];
            const status = typeof rawStatus === 'string' ? rawStatus : (rawStatus || 'Error');
            const color = getStatusColor(status);
            return (
              <li key={idx} style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: color, marginRight: '8px' }}></span>
                Build #{build.build_num}: <a href={allureUrl} target="_blank" rel="noreferrer" className="ms-1">Allure Report</a> - {status}
                {(status.toLowerCase() === 'running' || status.toLowerCase() === 'loading...') && (
                  <Button size="sm" className="ms-2" onClick={() => refreshBuildStatus(build.build_num)}>Refresh</Button>
                )}
              </li>
            );
          })}
        </ul>
        <Button onClick={handleRun}>Run Saved Job</Button>
      </>
    ) : (
      <Alert variant="warning">Job not found. Please create it first.</Alert>
    )}

    {/* ✅ Toast appears regardless of which content is visible */}
    <ToastContainer position="top-end" className="p-3">
      <Toast
        show={showSuccessToast}
        onClose={() => setShowSuccessToast(false)}
        delay={2000}
        autohide
        bg="success"
      >
        <Toast.Body className="text-white">Job started successfully!</Toast.Body>
      </Toast>
    </ToastContainer>
  </Container>
  );
};

export default JobDetailPage;
