import React from 'react';
import { Link, useLocation } from 'react-router-dom';

/**
 * Navigation Component
 * Provides accessible links to the main application modules: Dashboard, Profile, and AI Consultant.
 * Uses the current location to apply active styling.
 */
const Navigation = () => {
  const location = useLocation();

  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: 'grid_view' },
    { name: 'Hồ sơ', path: '/profile', icon: 'account_circle' },
    { name: 'Tư vấn AI', path: '/consultant', icon: 'psychology' },
  ];

  return (
    <nav className="flex items-center gap-2 p-1.5 bg-white rounded-2xl border border-slate-200 shadow-sm">
      {navItems.map((item) => (
        <Link
          key={item.path}
          to={item.path}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-bold transition-all duration-200 ${
            location.pathname === item.path
              ? 'bg-[#003466] text-white shadow-lg shadow-blue-900/20'
              : 'text-slate-500 hover:bg-slate-50 hover:text-[#003466]'
          }`}
        >
          <span className="material-symbols-outlined text-[20px]">{item.icon}</span>
          <span>{item.name}</span>
        </Link>
      ))}
    </nav>
  );
};

export default Navigation;