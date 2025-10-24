import React, { useState } from 'react';
interface NickNamePageProps {
  onSubmit: (nickname: string) => void;
}

const NickNamePage: React.FC<NickNamePageProps> = ({ onSubmit }) => {
  const [nicknameInput, setNicknameInput] = useState('');

  const handleNicknameChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setNicknameInput(event.target.value);
  };

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    onSubmit(nicknameInput);
  };

  return (
    <form className="nickname-form" onSubmit={handleSubmit}>
      <input
        id="nicknameInput"
        className="nickname-input"
        type="text"
        value={nicknameInput}
        onChange={handleNicknameChange}
        placeholder="Enter your nickname"
        autoComplete="off"
      />
      <button type="submit" className="nickname-button">
        Login
      </button>
    </form>
  );
};

export default NickNamePage;
