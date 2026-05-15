import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { KeyRound, ShieldCheck } from 'lucide-react';
import LoadingSpinner from '../components/LoadingSpinner';
import { useAuth } from '../context/AuthContext';

const inputClass = 'w-full px-4 py-3 bg-[#F1F5F9] border border-[#737781] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003466]/10 focus:border-[#003466] transition-all';

const AdminSignupPage = () => {
  const navigate = useNavigate();
  const { adminSignup, error, loading } = useAuth();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [adminKey, setAdminKey] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await adminSignup(fullName, email, password, adminKey);
      navigate('/login');
    } catch (err) {
      // Error state and toast are handled by AuthContext.
    }
  };

  return (
    <div className="min-h-screen bg-[#f8f9ff] flex items-center justify-center p-4 font-inter">
      <div className="bg-white border border-[#E2E8F0] rounded-2xl p-8 w-full max-w-[460px] shadow-sm">
        <header className="text-center mb-8">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-[#003466] text-white">
            <ShieldCheck size={24} aria-hidden="true" />
          </div>
          <h2 className="text-[30px] font-bold text-[#003466] mb-2 leading-tight">
            Create admin account
          </h2>
          <p className="text-base text-[#424750] leading-relaxed">
            Use the private admin signup key to create a new administrator.
          </p>
        </header>

        {error && (
          <div className="bg-error-container text-error p-3 rounded-lg text-sm mb-6 flex items-center gap-2 border border-error/20">
            <span className="material-symbols-outlined text-[18px]">error</span>
            <span className="flex-1">
              {typeof error === 'string' ? error : JSON.stringify(error)}
            </span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="space-y-2">
            <label className="block text-sm font-semibold text-[#0d1c2e]">Full name</label>
            <input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className={inputClass}
              placeholder="Admin User"
              required
            />
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-semibold text-[#0d1c2e]">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className={inputClass}
              placeholder="admin@vinuni.edu.vn"
              required
            />
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-semibold text-[#0d1c2e]">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className={inputClass}
              required
            />
            <p className="text-[11px] text-[#64748b] leading-relaxed italic">
              Minimum 8 characters with uppercase, lowercase, number, and special character.
            </p>
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-semibold text-[#0d1c2e]">Admin signup key</label>
            <input
              type="password"
              value={adminKey}
              onChange={(e) => setAdminKey(e.target.value)}
              className={inputClass}
              placeholder="ADMIN_SIGNUP_KEY"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3.5 bg-[#003466] text-white rounded-lg font-bold hover:bg-[#1a4b84] transition-all shadow-md active:scale-[0.98] disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <LoadingSpinner size="sm" color="white" />
                <span>Creating account...</span>
              </>
            ) : (
              <>
                <KeyRound size={18} aria-hidden="true" />
                <span>Create admin</span>
              </>
            )}
          </button>
        </form>

        <div className="mt-8 text-center text-sm text-[#424750]">
          Already have an account?
          <Link to="/login" className="ml-1 text-[#003466] font-bold hover:underline">
            Sign in
          </Link>
        </div>
      </div>
    </div>
  );
};

export default AdminSignupPage;
