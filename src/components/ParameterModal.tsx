// ParameterModal.tsx
import React, { useState, useEffect } from 'react';
import { Modal, Button, Form } from 'react-bootstrap';

interface ParameterModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (params: { [key: string]: string }) => void;
  requiredParams: {
    _class: string;
    name: string;
    description?: string;
    defaultParameterValue?: {
      _class: string;
      name: string;
      value: string;
    };
    choices?: string[];
    type?: string;
  }[];
}

const ParameterModal: React.FC<ParameterModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  requiredParams,
}) => {
  const [manualParams, setManualParams] = useState<{ [key: string]: string }>({});
  const [jsonText, setJsonText] = useState<string>('');
  const [useFile, setUseFile] = useState<boolean>(false);
  const [fileContent, setFileContent] = useState<string>('');

  useEffect(() => {
    const initial: { [key: string]: string } = {};
    requiredParams.forEach(p => {
      initial[p.name] = p.defaultParameterValue ? p.defaultParameterValue.value : '';
    });
    setManualParams(initial);
    setJsonText(JSON.stringify(initial, null, 2));
  }, [requiredParams]);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files && e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = evt => {
        const content = evt.target?.result as string;
        setFileContent(content);
      };
      reader.readAsText(file);
    }
  };

  const handleManualChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    const newParams = { ...manualParams, [name]: value };
    setManualParams(newParams);
    setJsonText(JSON.stringify(newParams, null, 2));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    let paramsObj: { [key: string]: string } = {};
    try {
      if (useFile) {
        if (!fileContent) {
          alert("Please upload a valid YAML/JSON file.");
          return;
        }
        // For simplicity, assume JSON parsing (replace with YAML parser if needed)
        paramsObj = JSON.parse(fileContent);
      } else {
        if (!jsonText) {
          alert("Please enter valid JSON.");
          return;
        }
        paramsObj = JSON.parse(jsonText);
      }
    } catch (err) {
      alert("Invalid JSON. Please check your input.");
      return;
    }
    onSubmit(paramsObj);
  };

  return (
    <Modal show={isOpen} onHide={onClose} size="lg">
      <Modal.Header closeButton>
        <Modal.Title>Enter Build Parameters</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <Form onSubmit={handleSubmit}>
          <Form.Group controlId="modeToggle">
            <Form.Check
              type="radio"
              label="Enter JSON manually"
              name="mode"
              checked={!useFile}
              onChange={() => setUseFile(false)}
            />
            <Form.Check
              type="radio"
              label="Upload YAML/JSON file"
              name="mode"
              checked={useFile}
              onChange={() => setUseFile(true)}
            />
          </Form.Group>
          {!useFile ? (
            <>
              <Form.Group controlId="manualFields">
                {requiredParams.map((param, idx) => (
                  <Form.Group key={idx} controlId={`param-${param.name}`} className="mb-2">
                    <Form.Label>
                      {param.name} {param.description ? `(${param.description})` : ''}
                    </Form.Label>
                    {param.choices ? (
                      <Form.Control
                        as="select"
                        name={param.name}
                        value={manualParams[param.name] || ''}
                        onChange={handleManualChange}
                      >
                        {param.choices.map((choice: string, i: number) => (
                          <option key={i} value={choice}>{choice}</option>
                        ))}
                      </Form.Control>
                    ) : (
                      <Form.Control
                        type="text"
                        name={param.name}
                        value={manualParams[param.name] || ''}
                        onChange={handleManualChange}
                      />
                    )}
                  </Form.Group>
                ))}
              </Form.Group>
              <Form.Group controlId="jsonTextarea" className="mt-2">
                <Form.Label>Or Edit JSON Directly</Form.Label>
                <Form.Control
                  as="textarea"
                  rows={8}
                  value={jsonText}
                  onChange={(e) => setJsonText(e.target.value)}
                />
              </Form.Group>
            </>
          ) : (
            <Form.Group controlId="fileUpload">
              <Form.Label>Upload YAML/JSON file</Form.Label>
              <Form.Control
                type="file"
                accept=".json,.yaml,.yml"
                onChange={handleFileUpload}
              />
            </Form.Group>
          )}
          <Button variant="primary" type="submit" className="mt-3">
            Submit Parameters
          </Button>
        </Form>
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={onClose}>
          Cancel
        </Button>
      </Modal.Footer>
    </Modal>
  );
};

export default ParameterModal;
