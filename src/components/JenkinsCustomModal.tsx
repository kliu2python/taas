import React from 'react';
import { Modal, Form, Button } from 'react-bootstrap';

type CustomEnv = {
  docker_tag: string;
  fgt_ftm_dns: string;
  fortigate_ip: string;
  fac_ip: string;
  fac_api_key: string;
};

interface Props {
  show: boolean;
  onClose: () => void;
  onSave: () => void;
  customEnv: CustomEnv;
  setCustomEnv: React.Dispatch<React.SetStateAction<CustomEnv>>;
}

const CustomEnvModal: React.FC<Props> = ({ show, onClose, onSave, customEnv, setCustomEnv }) => {
  return (
    <Modal show={show} onHide={onClose} centered>
      <Modal.Header closeButton>
        <Modal.Title>Custom Environment Setup</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        {Object.entries(customEnv).map(([key, value]) => (
          <Form.Group key={key} className="mb-3">
            <Form.Label>{key}</Form.Label>
            <Form.Control
              type="text"
              placeholder={`Enter ${key}`}
              value={value}
              onChange={(e) =>
                setCustomEnv((prev) => ({ ...prev, [key]: e.target.value }))
              }
            />
          </Form.Group>
        ))}
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={onClose}>Cancel</Button>
        <Button variant="primary" onClick={onSave}>Save</Button>
      </Modal.Footer>
    </Modal>
  );
};

export default CustomEnvModal;
