const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const login = async (email, password) => {
  const response = await fetch(`${API_URL}/api/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password }),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.message || 'Email hoặc mật khẩu không chính xác');
  return data;
};

export const signup = async (fullName, email, password) => {
  const response = await fetch(`${API_URL}/api/auth/signup`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ full_name: fullName, email, password }),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.message || 'Đăng ký không thành công');
  return data;
};