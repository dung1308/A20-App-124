import React from 'react';
import { Link } from 'react-router-dom';
import { useStore } from '../../state/store';

const UpperPanel = ({ activeLink }) => {
  const { userId, role } = useStore();

  return (
    <header className="h-16 px-8 flex justify-between items-center bg-white/95 backdrop-blur-md border-b border-slate-200 z-10 flex-shrink-0">
      <div className="flex items-center gap-4">
        <h1 className="text-xl font-black tracking-tighter text-blue-900">Brilliant Mentor</h1>
        <nav className="hidden lg:flex items-center gap-6 ml-8">
          <Link to="/wizard" className={`text-sm font-medium ${activeLink === 'home' ? 'text-blue-700 border-b-2 border-blue-700 pb-1' : 'text-slate-600 hover:text-blue-700'}`}>Preferences Change</Link>
          <a href="#" className={`text-sm font-medium ${activeLink === 'major-guide' ? 'text-blue-700 border-b-2 border-blue-700 pb-1' : 'text-slate-600 hover:text-blue-700'}`}>Major Guide</a>
          <Link to="/consultant" className={`text-sm font-medium ${activeLink === 'consultation' ? 'text-blue-700 border-b-2 border-blue-700 pb-1' : 'text-slate-600 hover:text-blue-700'}`}>Consultation</Link>
        </nav>
      </div>
    </header>
  );
};

export default UpperPanel;