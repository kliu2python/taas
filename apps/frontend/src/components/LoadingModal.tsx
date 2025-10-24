import React from 'react';
import { Modal, Spinner } from 'react-bootstrap';

interface LoadingModalProps {
  isOpen: boolean;
}

const LoadingModal: React.FC<LoadingModalProps> = ({ isOpen }) => {
  return (
    <Modal show={isOpen} backdrop="static" keyboard={false} centered>
      <Modal.Body className="d-flex justify-content-center align-items-center">
        <Spinner animation="border" role="status">
          <span className="visually-hidden">Loading...</span>
        </Spinner>
      </Modal.Body>
    </Modal>
  );
};

export default LoadingModal;