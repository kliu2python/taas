import React, { useEffect, useState } from 'react';
import {
  Container,
  Form,
  Button,
  Spinner,
  Row,
  Col,
  Toast,
  ToastContainer,
  InputGroup
} from 'react-bootstrap';
import axios from 'axios';

import config from '../config/config';
import CustomEnvModal from './JenkinsCustomModal';
import UploadFileModal from './UploadFileModal';
import TestResultsModal from './JenkinsResultModal';

const JenkinsFTMIOS: React.FC = () => {
  const [imageOptions, setImageOptions] = useState<string[]>([]);
  const [selectedImage, setSelectedImage] = useState('');
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  const [toastVariant, setToastVariant] = useState<'success' | 'danger'>('success');
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [selectedEnv, setSelectedEnv] = useState<'Prod' | 'QA' | 'Custom' | ''>('');
  const [showCustomEnvModal, setShowCustomEnvModal] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState('');
  const [customEnv, setCustomEnv] = useState({
    docker_tag: '',
    fgt_ftm_dns: '',
    fortigate_ip: '',
    fac_ip: '',
    fac_api_key: ''
  });
  const [testResultLogs, setTestResultLogs] = useState<any[]>([]);
  const [refreshingIndex, setRefreshingIndex] = useState<number | null>(null);
  const [showResultsModal, setShowResultsModal] = useState(false);
  const [selectedScope, setSelectedScope] = useState<'Functional' | 'Integration' | 'Regression' | 'Acceptable' | ''>('');


  const ipaOptions = imageOptions.filter(name => name.endsWith('.ipa'));
  const isReadyToRun = selectedEnv && selectedImage && selectedProduct && selectedPlatforms.length > 0;

  useEffect(() => {
    axios.get(`http://10.160.24.88:31224/api/v1/jenkins_cloud/apk_images`)
      .then(res => setImageOptions(res.data))
      .catch(err => console.error(err));
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      fetchResults();
    }, 5 * 60 * 1000);

    return () => clearInterval(interval);
  }, []);

  const handlePlatformChange = (platform: string) => {
    setSelectedPlatforms(prev =>
      prev.includes(platform)
        ? prev.filter(p => p !== platform)
        : [...prev, platform]
    );
  };

  const handleSubmit = () => {
    setIsSubmitting(true);

    const nonEmptyCustomEnv = Object.fromEntries(
      Object.entries(customEnv).filter(([_, v]) => v.trim() !== '')
    );

    const payload: any = {
      parameters: {
        RUN_STAGE: selectedProduct,
        ftm_ipa_version: selectedImage
      },
      platforms: selectedPlatforms,
      environment: selectedEnv,
      custom: setShowCustomEnvModal
    };

    if (Object.keys(nonEmptyCustomEnv).length > 0) {
      payload.custom_env = nonEmptyCustomEnv;
    }

    axios.post(`${config.jenkinsCloudUrl}/api/v1/jenkins_cloud/run/execute/ftm`, payload)
      .then(() => {
        setToastMessage('Job started successfully');
        setToastVariant('success');
      })
      .catch(err => {
        setToastMessage(`Error: ${err.message}`);
        setToastVariant('danger');
      })
      .finally(() => {
        setIsSubmitting(false);
        setShowToast(true);
      });
  };

  const fetchResults = async () => {
    try {
      const res = await axios.get(`${config.jenkinsCloudUrl}/api/v1/jenkins_cloud/run/results/ios/ftm`);
      setTestResultLogs(res.data || []);
      if (res.status === 200) {
        setToastMessage('Refresh Completed');
        setToastVariant('success');
        setShowToast(true);
      }
    } catch (err) {
      if (axios.isAxiosError(err)) {
        setTestResultLogs([{ res: `Failed to fetch results: ${err.message}` }]);
        setToastMessage(`Error: ${err.message}`);
      } else {
        setToastMessage('An unknown error occurred');
      }
      setToastVariant('danger');
      setShowToast(true);
    }
  };

  const refreshSingleJob = (jobName: string, index: number) => {
    setRefreshingIndex(index);
    axios.get(`${config.jenkinsCloudUrl}/api/v1/jenkins_cloud/run/result/ios/ftm?job_name=${jobName}`)
      .then(res => {
        const newLogs = [...testResultLogs];
        setTestResultLogs(newLogs);
        setToastMessage('Completed Refresh');
        fetchResults();
      })
      .catch(err => console.error(`Refresh failed for ${jobName}:`, err))
      .finally(() => setRefreshingIndex(null));
  };

  const deleteSingleResult = (jobName: string, index: number) => {
    setRefreshingIndex(index);
    axios.delete(`${config.jenkinsCloudUrl}/api/v1/jenkins_cloud/run/result/ios/ftm/delete?job_name=${jobName}`)
      .then(res => {
        const newLogs = [...testResultLogs];
        newLogs[index].res = res.data;
        setTestResultLogs(newLogs);
        fetchResults();
      })
      .catch(err => console.error(`Refresh failed for ${jobName}:`, err))
      .finally(() => setRefreshingIndex(null));
  };

  const uploadFileToServer = (file: File) => {
    setIsUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    axios.post(`${config.jenkinsCloudUrl}/api/v1/jenkins_cloud/apk_images`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
      .then(() => {
        setSelectedImage(file.name);
        setImageOptions(prev => [...new Set([...prev, file.name])]);
        setToastMessage(`Uploaded: ${file.name}`);
        setToastVariant('success');
        axios.get(`${config.jenkinsCloudUrl}/api/v1/jenkins_cloud/apk_images`)
          .then(res => setImageOptions(res.data));
      })
      .catch((err) => {
        setToastMessage(`Upload failed: ${err.message}`);
        setToastVariant('danger');
      })
      .finally(() => {
        setIsUploading(false);
        setShowUploadModal(false);
        setShowToast(true);
      });
  };

  return (
    <Container className="p-4 position-relative">
      {/* Select Test Environment */}
      <Form.Group className="mb-3">
        <Form.Label>Select Test Environment *</Form.Label>
        <Row>
          {['Prod', 'QA', 'Custom'].map((env) => (
            <Col key={env} xs="auto">
              <Form.Check
                type="radio"
                label={env}
                name="environment"
                value={env}
                checked={selectedEnv === env}
                onChange={() => {
                  setSelectedEnv(env as 'Prod' | 'QA' | 'Custom');
                  if (env === 'Custom') setShowCustomEnvModal(true);
                }}
              />
            </Col>
          ))}
        </Row>
      </Form.Group>

      {/* Select or Enter IPA File */}
      <Form.Group className="mb-3">
        <Form.Label>Select or Enter IPA File *</Form.Label>
        <InputGroup>
          <Form.Control
            list="ipa-suggestions"
            value={selectedImage}
            onChange={(e) => setSelectedImage(e.target.value)}
            placeholder="Start typing IPA file name..."
          />
          <Button variant="outline-primary" onClick={() => setShowUploadModal(true)}>
            Upload New IPA
          </Button>
        </InputGroup>
        <datalist id="ipa-suggestions">
          {ipaOptions.map((file, idx) => (
            <option key={idx} value={file} />
          ))}
        </datalist>
      </Form.Group>

      <Form.Group className="mb-3">
        <Form.Label>Select Test Scope *</Form.Label>
        <Form.Select
            value={selectedScope}
            onChange={(e) => {
            const scope = e.target.value as typeof selectedScope;
            setSelectedScope(scope);

            switch (scope) {
                case 'Functional':
                setSelectedProduct('ALL');
                break;
                case 'Integration':
                setSelectedProduct('');
                break;
                case 'Regression':
                setSelectedProduct('');
                break;
                case 'Acceptable':
                setSelectedProduct('FortiGate');
                break;
                default:
                setSelectedProduct('');
            }
            }}
        >
            <option value="">-- Select Test Scope --</option>
            <option value="Functional">Functional Test (more test cases)</option>
            <option value="Integration">Integration Test</option>
            <option value="Regression">Regression Test</option>
            <option value="Acceptable">Acceptable Test (less test cases)</option>
        </Form.Select>
        </Form.Group>


        <Form.Group className="mb-3">
        <Form.Label>Select Testing Product *</Form.Label>
        <Form.Select
            value={selectedProduct}
            onChange={(e) => setSelectedProduct(e.target.value)}
            disabled={
            selectedScope === '' || selectedScope === 'Acceptable' || 
            (selectedScope === 'Functional' && selectedProduct === 'ALL')
            }
        >
            <option value="">-- Select Testing Product --</option>
            {(() => {
            const allOptions = [
                'ALL',
                'FortiGate',
                'FortiAuthenticator',
                'FortiTokenCloud_FAC',
                'FortiTokenCloud_FGT',
                'FortiToken',
                'FortiToken Cloud'
            ];

            if (selectedScope === 'Functional') {
                return <option value="ALL">ALL</option>;
            }

            if (selectedScope === 'Integration') {
                return allOptions
                .filter(opt => opt !== 'ALL')
                .map((prod, idx) => <option key={idx} value={prod}>{prod}</option>);
            }

            if (selectedScope === 'Regression') {
                return ['FortiToken', 'FortiToken Cloud']
                .map((prod, idx) => <option key={idx} value={prod}>{prod}</option>);
            }

            if (selectedScope === 'Acceptable') {
                return <option value="FortiGate">FortiGate</option>;
            }

            return null;
            })()}
        </Form.Select>
        </Form.Group>


      {/* Select Test Platforms */}
      <Form.Group className="mb-3">
        <Form.Label>Select Test Platforms *</Form.Label>
        <Row>
          {['ios16', 'ios17', 'ios18'].map((platform, idx) => (
            <Col key={idx} xs="auto">
              <Form.Check
                type="checkbox"
                label={platform}
                checked={selectedPlatforms.includes(platform)}
                onChange={() => handlePlatformChange(platform)}
              />
            </Col>
          ))}
        </Row>
      </Form.Group>

      {/* Run Job Button */}
      <Button onClick={handleSubmit} disabled={!isReadyToRun || isSubmitting}>
        {isSubmitting ? <Spinner animation="border" size="sm" /> : 'Run Job'}
      </Button>

      <Button variant="info" className="ms-2" onClick={async () => {
        await fetchResults();
        setShowResultsModal(true);
      }}>
        View Test Results
      </Button>

      <CustomEnvModal
        show={showCustomEnvModal}
        onClose={() => setShowCustomEnvModal(false)}
        onSave={() => setShowCustomEnvModal(false)} // You can extend this logic
        customEnv={customEnv}
        setCustomEnv={setCustomEnv}
        />

      <UploadFileModal
        show={showUploadModal}
        isUploading={isUploading}
        uploadFile={uploadFile}
        setUploadFile={setUploadFile}
        onUpload={() => uploadFile && uploadFileToServer(uploadFile)}
        onClose={() => setShowUploadModal(false)}
        accept=".ipa" // You can now customize this per use case
        />

      {/* Toast Messages */}
      <ToastContainer position="top-end" className="p-3">
        <Toast
          show={showToast}
          onClose={() => setShowToast(false)}
          delay={3000}
          autohide
          bg={toastVariant}
        >
          <Toast.Body className="text-white">{toastMessage}</Toast.Body>
        </Toast>
      </ToastContainer>

      <TestResultsModal
        show={showResultsModal}
        onClose={() => setShowResultsModal(false)}
        testResultLogs={testResultLogs}
        onRefreshAll={fetchResults}
        onRefreshSingle={refreshSingleJob}
        refreshingIndex={refreshingIndex}
        deleteSingleResult={deleteSingleResult}
        />
    </Container>
  );
};

export default JenkinsFTMIOS;
