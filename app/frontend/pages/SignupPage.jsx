import React, { useState } from 'react';
import { signup } from '../services/auth';

const SignupPage = ({ onSignupSuccess }) => {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await signup(fullName, email, password);
      onSignupSuccess();
    } catch (err) {
      // Extract specific error messages from the backend response
      if (err.response?.data?.detail) {
        const detail = err.response.data.detail;
        if (Array.isArray(detail)) {
          // Join multiple validation error messages (like password requirements)
          setError(detail.map(d => d.msg).join(' '));
        } else {
          // Handle single string detail (like "Email already registered")
          setError(detail);
        }
      } else {
        setError('Đăng ký không thành công. Vui lòng thử lại.');
      }
    }
  };

  const containerStyle = {
    maxWidth: '400px',
    margin: '80px auto',
    padding: '40px 24px',
    border: '1px solid #e5e7eb',
    borderRadius: '10px',
    fontFamily: 'system-ui, -apple-system, sans-serif'
  };

  const inputStyle = {
    width: '100%',
    padding: '12px',
    marginBottom: '16px',
    border: '1px solid #e5e7eb',
    borderRadius: '6px',
    boxSizing: 'border-box'
  };

  const buttonStyle = {
    width: '100%',
    padding: '12px',
    backgroundColor: '#1a1a1a',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    fontWeight: '600'
  };

  const bubbleStyle = {
    fontSize: '12px',
    color: '#d93025',
    backgroundColor: '#fff',
    padding: '8px 12px',
    borderRadius: '4px',
    border: '1px solid #d93025',
    marginTop: '8px',
    marginBottom: '16px',
    lineHeight: '1.4',
    display: 'flex',
    gap: '8px',
    alignItems: 'center',
    position: 'relative',
    boxShadow: '0 1px 2px rgba(60,64,67,0.3)'
  };

  const triangleStyle = {
    position: 'absolute',
    top: '-6px',
    left: '12px',
    width: '0',
    height: '0',
    borderLeft: '6px solid transparent',
    borderRight: '6px solid transparent',
    borderBottom: '6px solid #d93025'
  };

  const triangleInnerStyle = {
    position: 'absolute',
    top: '1px',
    left: '-6px',
    borderLeft: '6px solid transparent',
    borderRight: '6px solid transparent',
    borderBottom: '6px solid #fff'
  };

  return (
    <div style={containerStyle}>
      <h2 style={{ marginBottom: '24px', textAlign: 'center' }}>Đăng ký tài khoản</h2>
      {error && <p style={{ color: '#dc2626', fontSize: '14px', marginBottom: '16px' }}>{error}</p>}
      <form onSubmit={handleSubmit}>
        <label style={{ display: 'block', marginBottom: '8px', color: '#6b7280' }}>Họ và tên</label>
        <input type="text" value={fullName} onChange={(e) => setFullName(e.target.value)} style={inputStyle} required />

        <label style={{ display: 'block', marginBottom: '8px', color: '#6b7280' }}>Email</label>
        <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} style={inputStyle} required />
        
        <label style={{ display: 'block', marginBottom: '8px', color: error ? '#d93025' : '#6b7280' }}>Mật khẩu</label>
        <input 
          type="password" 
          value={password} 
          onChange={(e) => setPassword(e.target.value)} 
          style={{
            ...inputStyle, 
            borderColor: error ? '#d93025' : '#e5e7eb', 
            marginBottom: error ? '4px' : '16px'
          }} 
          required 
        />

        {error && (
          <div style={{ position: 'relative' }}>
            <div style={triangleStyle}><div style={triangleInnerStyle}></div></div>
            <div style={bubbleStyle}>
              <span className="material-symbols-outlined" style={{ fontSize: '18px', color: '#d93025' }}>error</span>
              <p style={{ margin: 0 }}>Mật khẩu cần ít nhất 8 ký tự, bao gồm chữ cái in hoa, chữ thường, chữ số và ký tự đặc biệt (VD: !@#$).</p>
            </div>
          </div>
        )}
        
        <button type="submit" style={buttonStyle}>Đăng ký</button>
      </form>
    </div>
  );
};

export default SignupPage;