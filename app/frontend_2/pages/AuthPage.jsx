import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useStore } from '../state/store';
import { login, signup } from './auth';

const AuthPage = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    password: ''
  });
  // Use selector pattern for better reliability and performance
  const setUserId = useStore((state) => state.setUserId || state.setUser);
  const setRole = useStore((state) => state.setRole);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const data = isLogin 
        ? await login(formData.email, formData.password)
        : await signup(formData.full_name, formData.email, formData.password);

      if (isLogin) {
        localStorage.setItem('token', data.token);
        localStorage.setItem('user_email', data.user_email);
        localStorage.setItem('user_role', data.role || 'user');
        
        if (typeof setUserId === 'function') {
          setUserId(data.user_email); 
        }
        if (typeof setRole === 'function') {
          setRole(data.role || 'user');
        }
        
        navigate('/wizard');
      } else {
        setIsLogin(true);
        alert('Đăng ký thành công! Vui lòng đăng nhập.');
      }
    } catch (error) {
      console.error('Auth error:', error);
      alert(error.message || 'Lỗi kết nối đến máy chủ.');
    }
  };

  return (
    <div className="min-h-screen bg-[#f8f9ff] flex items-center justify-center p-4 font-inter">
      <div className="bg-white border border-[#E2E8F0] rounded-2xl p-8 w-full max-w-[440px] shadow-sm">
        <h2 className="text-[30px] font-semibold text-[#0d1c2e] text-center mb-2 leading-tight">
          {isLogin ? 'Chào mừng trở lại' : 'Tạo tài khoản'}
        </h2>
        <p className="text-base text-[#424750] text-center mb-8 leading-relaxed">
          {isLogin 
            ? 'Vui lòng đăng nhập để tiếp tục hành trình của bạn.' 
            : 'Bắt đầu quá trình xét tuyển cùng AI Mentor.'}
        </p>

        <form onSubmit={handleSubmit} className="space-y-5">
          {!isLogin && (
            <div className="space-y-2">
              <label className="block text-sm font-medium text-[#0d1c2e]">Họ và tên</label>
              <input 
                type="text" 
                required
                placeholder="Nguyễn Văn A" 
                value={formData.full_name}
                onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                className="w-full px-4 py-3 bg-[#F1F5F9] border border-[#737781] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003466]/10 focus:border-[#003466] transition-all"
              />
            </div>
          )}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-[#0d1c2e]">Email</label>
            <input 
              type="email" 
              required
              placeholder="student@vinuni.edu.vn" 
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="w-full px-4 py-3 bg-[#F1F5F9] border border-[#737781] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003466]/10 focus:border-[#003466] transition-all"
            />
          </div>
          <div className="space-y-2">
            <label className="block text-sm font-medium text-[#0d1c2e]">Mật khẩu</label>
            <input 
              type="password" 
              required
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              className="w-full px-4 py-3 bg-[#F1F5F9] border border-[#737781] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003466]/10 focus:border-[#003466] transition-all"
            />
          </div>
          <button 
            type="submit" 
            className="w-full py-3.5 bg-[#003466] text-white rounded-lg font-semibold hover:opacity-90 transition-opacity mt-3"
          >
            {isLogin ? 'Đăng nhập' : 'Đăng ký'}
          </button>
        </form>

        <div className="mt-6 text-center text-sm text-[#424750]">
          {isLogin ? 'Chưa có tài khoản?' : 'Đã có tài khoản?'}
          <button 
            onClick={() => setIsLogin(!isLogin)}
            className="ml-1 text-[#003466] font-semibold hover:underline"
          >
            {isLogin ? 'Đăng ký ngay' : 'Đăng nhập'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default AuthPage;