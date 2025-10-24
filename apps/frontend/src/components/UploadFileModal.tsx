import React from 'react';
import { Modal, Form, Button, Spinner } from 'react-bootstrap';

interface UploadFileModalProps {
  show: boolean;
  isUploading: boolean;
  uploadFile: File | null;
  setUploadFile: (file: File | null) => void;
  onUpload: () => void;
  onClose: () => void;
  accept?: string; // <- Optional accept prop
}

const UploadFileModal: React.FC<UploadFileModalProps> = ({
  show,
  isUploading,
  uploadFile,
  setUploadFile,
  onUpload,
  onClose,
  accept = '.ipa', // <- Default to '.ipa'
}) => {
  return (
    <Modal show={show} onHide={() => !isUploading && onClose()} centered backdrop="static">
      <Modal.Header closeButton={!isUploading}>
        <Modal.Title>Upload File</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <Form.Group>
          <Form.Label>Select file to upload</Form.Label>
          <Form.Control
            type="file"
            accept={accept}
            onChange={(e) => {
              const input = e.target as HTMLInputElement;
              const file = input.files?.[0] || null;
              setUploadFile(file);
            }}
            disabled={isUploading}
          />
        </Form.Group>
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={onClose} disabled={isUploading}>
          Cancel
        </Button>
        <Button
          variant="primary"
          onClick={onUpload}
          disabled={!uploadFile || isUploading}
        >
          {isUploading ? <Spinner animation="border" size="sm" /> : 'Upload'}
        </Button>
      </Modal.Footer>
    </Modal>
  );
};

export default UploadFileModal;
