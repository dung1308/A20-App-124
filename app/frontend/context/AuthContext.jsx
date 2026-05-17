import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import axios from 'axios';

// Create an Axios instance for authentication that doesn't use the interceptor yet
// to avoid circular dependencies or issues during token acquisition.
const authApi = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'https://a20-app-124-production.up.railway.app',
});

// Create the Auth Context
const AuthContext = createContext(null);

// Custom hook to use the Auth Context
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Auth Provider Component
export const AuthProvider = ({ children }) => {
  const [isInitializing, setIsInitializing] = useState(true); // Initial mount-time check
  const [loading, setLoading] = useState(false); // Ongoing request state
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  // User-related states
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem('token'));
  const [userId, setUserId] = useState(localStorage.getItem('user_email'));
  const [role, setRole] = useState(localStorage.getItem('user_role'));
  const [userName, setUserName] = useState(localStorage.getItem('user_name'));
  const [userAvatar, setUserAvatar] = useState(localStorage.getItem('user_avatar'));
  const [permissions, setPermissions] = useState(JSON.parse(localStorage.getItem('user_permissions') || '[]'));

  // Helper to decode JWT and update user states
  const decodeTokenAndSetUser = useCallback((jwtToken) => {
    if (!jwtToken) {
      setUserId(null);
      setRole(null);
      setUserName(null);
      setUserAvatar(null);
      setPermissions([]);
      setIsAuthenticated(false);
      return;
    }
    try {
      const payload = JSON.parse(atob(jwtToken.split('.')[1]));
      
      setUserId(payload.sub);
      setRole(payload.role || 'user');
      setPermissions(payload.permissions || []);
      // full_name and picture might not be in the token payload directly,
      // they are usually returned by the login endpoint.
      // For now, we rely on localStorage for these or the login response.
      setIsAuthenticated(true);
    } catch (e) {
      console.error("Error decoding token:", e);
      // If token is invalid, clear it
      localStorage.removeItem('token');
      localStorage.removeItem('user_email');
      localStorage.removeItem('user_role');
      localStorage.removeItem('user_name');
      localStorage.removeItem('user_avatar');
      localStorage.removeItem('user_permissions');
      setToken(null);
      setUserId(null);
      setRole(null);
      setUserName(null);
      setUserAvatar(null);
      setPermissions([]);
      setIsAuthenticated(false);
    }
  }, []);

  // Effect to initialize auth state from localStorage on mount
  useEffect(() => {
    const storedToken = localStorage.getItem('token');
    if (storedToken) {
      setToken(storedToken);
      decodeTokenAndSetUser(storedToken);
    }
    setIsInitializing(false); // Finished initial loading
  }, [decodeTokenAndSetUser]);

  // Helper function to handle successful authentication (login/signup/google)
  const handleAuthSuccess = useCallback((data) => {
    const newToken = data.token;
    const savedAvatar = localStorage.getItem(`user_avatar_${data.user_email}`);
    const avatar = savedAvatar || data.picture || '';
    localStorage.setItem('token', newToken);
    localStorage.setItem('user_email', data.user_email);
    localStorage.setItem('user_role', data.role || 'user');
    localStorage.setItem('user_name', data.full_name || '');
    localStorage.setItem('user_avatar', avatar);
    localStorage.setItem('user_permissions', JSON.stringify(data.permissions || []));

    setToken(newToken);
    setIsAuthenticated(true);
    setUserId(data.user_email);
    setRole(data.role || 'user');
    setUserName(data.full_name || null);
    setUserAvatar(avatar || null);
    setPermissions(data.permissions || []);

    // Navigate based on Wizard completion
    const isWizardCompleted = localStorage.getItem(`wizard_completed_${data.user_email}`) === 'true';
    navigate(isWizardCompleted ? '/dashboard' : '/wizard');
  }, [navigate]);

  const login = async (email, password) => {
    setLoading(true);
    setError(null);
    try {
      const response = await authApi.post('/api/auth/login', { email, password });
      handleAuthSuccess(response.data);
      toast.success('Đăng nhập thành công!');
      return response.data;
    } catch (err) {
      const detail = err.response?.data?.detail;
      const msg = Array.isArray(detail) 
        ? detail.map(d => d.msg.replace('Value error, ', '')).join(' ') 
        : (typeof detail === 'string' ? detail.replace('Value error, ', '') : (err.message || 'Email hoặc mật khẩu không chính xác'));
      setError(msg);
      toast.error(msg);
      throw new Error(msg);
    } finally {
      setLoading(false);
    }
  };

  const signup = async (fullName, email, password) => {
    setLoading(true);
    setError(null);
    try {
      const response = await authApi.post('/api/auth/signup', { full_name: fullName, email, password });
      toast.success('Đăng ký tài khoản thành công! Vui lòng đăng nhập.');
      // After signup, we don't automatically log in. User needs to manually login.
      return response.data;
    } catch (err) {
      const detail = err.response?.data?.detail;
      const msg = Array.isArray(detail) 
        ? detail.map(d => d.msg.replace('Value error, ', '')).join(' ') 
        : (typeof detail === 'string' ? detail.replace('Value error, ', '') : (err.message || 'Lỗi đăng ký tài khoản'));
      setError(msg);
      toast.error(msg);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const adminSignup = async (fullName, email, password, adminKey) => {
    setLoading(true);
    setError(null);
    try {
      const response = await authApi.post('/api/auth/admin-signup', {
        full_name: fullName,
        email,
        password,
        admin_key: adminKey,
      });
      toast.success('Admin account created. Please sign in.');
      return response.data;
    } catch (err) {
      const detail = err.response?.data?.detail;
      const msg = Array.isArray(detail)
        ? detail.map(d => d.msg.replace('Value error, ', '')).join(' ')
        : (typeof detail === 'string' ? detail.replace('Value error, ', '') : (err.message || 'Could not create admin account'));
      setError(msg);
      toast.error(msg);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const loginWithGoogle = async (credential) => {
    setLoading(true);
    setError(null);
    try {
      const response = await authApi.post('/api/auth/google', { token: credential });
      if (response.data.status !== 'success') {
        throw new Error(response.data.detail || 'Google login failed');
      }
      
      handleAuthSuccess(response.data);
      toast.success('Đăng nhập Google thành công!');
      return response.data;
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Đăng nhập Google thất bại';
      setError(msg);
      toast.error(msg);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const logout = useCallback(() => {
    localStorage.removeItem('token');
    localStorage.removeItem('user_email');
    localStorage.removeItem('user_role');
    localStorage.removeItem('user_name');
    localStorage.removeItem('user_avatar');
    localStorage.removeItem('user_permissions');
    setToken(null);
    setIsAuthenticated(false);
    setUserId(null);
    setRole(null);
    setUserName(null);
    setUserAvatar(null);
    setPermissions([]);
    toast.success('Đã đăng xuất');
    navigate('/login');
  }, [navigate]);

  const updateUserAvatar = useCallback((avatarDataUrl) => {
    const email = localStorage.getItem('user_email');
    if (email) {
      localStorage.setItem(`user_avatar_${email}`, avatarDataUrl || '');
    }
    localStorage.setItem('user_avatar', avatarDataUrl || '');
    setUserAvatar(avatarDataUrl || '');
  }, []);

  const authContextValue = {
    token,
    isAuthenticated,
    userId,
    role,
    userName,
    userAvatar,
    permissions,
    updateUserAvatar,
    login,
    signup,
    adminSignup,
    loginWithGoogle,
    logout,
    loading,
    error,
    setError,
  };

  if (isInitializing) {
    // You might want a global loading spinner here
    return <div>Loading authentication...</div>;
  }

  return (
    <AuthContext.Provider value={authContextValue}>
      {children}
    </AuthContext.Provider>
  );
};
