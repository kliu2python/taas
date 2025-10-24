import React, { useState, Fragment } from 'react';
import '../styles/CustomModal.css'

interface CustomModalProps {
  isOpen: boolean;
  onClose: () => void;
  onOSSubmit: (os: string) => void;
  onVersionSubmit: (os: string, version: string) => void;
  os: string | null;
}

const CustomModal: React.FC<CustomModalProps> = ({ isOpen, onClose, onOSSubmit, onVersionSubmit, os }) => {
  const [version, setVersion] = useState<string>('7');

  const handleOSSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const selectedOS = (e.target as any).os.value;
    onOSSubmit(selectedOS);
  };

  const handleVersionSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onVersionSubmit('android', version);
    onClose();
  };

  if (!isOpen) {
    return null;
  }

  return (
    <Fragment>
    <div className="overlay">
      <div className="overlay__background" />
      <div className="overlay__container">
        {os === null ? (
          <form onSubmit={handleOSSubmit} className="overlay__form">
            <h2>Select OS</h2>
            <label className="overlay__label">
              <input
                type="radio"
                name="os"
                value="android"
                className="overlay__input"
              />
              Android
            </label>
            <label className="overlay__label">
              <input
                type="radio"
                name="os"
                value="ios"
                className="overlay__input"
              />
              iOS
            </label>
            <div className="modal-buttons">
              <button type="submit" className="overlay__button">Next</button>
              <button type="button" onClick={onClose} className="overlay__button overlay__button--cancel">Cancel</button>
            </div>
          </form>
        ) : os === 'android' ? (
          <form onSubmit={handleVersionSubmit} className="overlay__form">
            <h2>Select Android Version</h2>
            <label className="overlay__label">
              <select value={version} onChange={(e) => setVersion(e.target.value)} className="overlay__select">
                  {['15', '14', '13', '12.1', '12', '11', '10', '9', '8.1', '8', '7.1', '7'].map((v) => (
                    <option key={v} value={v}>{`Android ${v}`}</option>
                  ))}
              </select>
            </label>
            <div className="modal-buttons">
              <button type="submit" className="overlay__button">Create</button>
              <button type="button" onClick={onClose} className="overlay__button overlay__button--cancel">Cancel</button>
            </div>
          </form>
        ) : (
          <div className="overlay__form">
            <h2>iOS Emulator</h2>
            <p>iOS emulator cloud is pending to be ready for use.</p>
            <div className="modal-buttons">
              <button type="button" onClick={onClose} className="overlay__button">Close</button>
            </div>
          </div>
        )}
      </div>
    </div>
  </Fragment>
  );
};

export default CustomModal;