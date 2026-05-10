import React from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import LeftPanel from '../components/panels/LeftPanel';
import Navigation from '../components/Navigation';

/**
 * AuthenticatedLayout Component
 * Shared wrapper for all protected routes. Includes the LeftPanel sidebar
 * and a header containing the Navigation component.
 */
const AuthenticatedLayout = () => {
  const navigate = useNavigate();
  const userEmail = localStorage.getItem('user_email') || 'User';

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user_email');
    localStorage.removeItem('user_role');
    navigate('/login');
  };

  return (
    <div className="authenticated-layout flex h-screen w-full overflow-hidden bg-slate-50 font-inter">
      {/* Shared Sidebar */}
      <LeftPanel />

      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Shared Top Header */}
        <header className="h-16 px-8 flex items-center justify-between bg-white border-b border-slate-200 flex-shrink-0">
          <div className="flex items-center gap-4">
            <h1 className="text-xl font-black text-[#003466] hidden md:block">VinUni Admission</h1>
          </div>
          
          <Navigation />
          
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-blue-50 flex items-center justify-center text-[#003466] font-bold text-sm border border-blue-100 shadow-sm">
              {userEmail.charAt(0).toUpperCase()}
            </div>
            <button 
              onClick={handleLogout}
              className="flex items-center gap-1 px-3 py-2 text-slate-500 hover:text-red-600 hover:bg-red-50 rounded-xl transition-all duration-200 text-sm font-bold"
              title="Đăng xuất"
            >
              <span className="material-symbols-outlined text-[20px]">logout</span>
              <span className="hidden lg:inline">Đăng xuất</span>
            </button>
          </div>
        </header>

        {/* Main Content Area - Outlet renders the child route component */}
        <div className="flex-1 flex flex-col overflow-hidden relative">
          <Outlet />
        </div>
      </div>
    </div>
  );
};

export default AuthenticatedLayout;