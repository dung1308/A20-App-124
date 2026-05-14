import React from 'react';
import { Link } from 'react-router-dom';
import { useStore } from '../../state/store';

const UpperPanel = () => {
  const { userId, role } = useStore();

  return (
    <header className="h-16 px-4 md:px-8 flex items-center bg-white/95 backdrop-blur-md border-b border-slate-200 z-10 flex-shrink-0">
      {/* Spacer to allow the fixed mobile menu button from LeftPanel to look integrated */}
      <div className="w-12 md:hidden"></div>
      <div className="flex-1 flex items-center justify-center md:justify-start gap-4">
        <h1 className="text-lg md:text-xl font-black tracking-tighter text-blue-900">VinUNI Admission</h1>
      </div>
      {/* Right side spacer to keep the title perfectly centered on mobile */}
      <div className="w-12 md:hidden"></div>
    </header>
  );
};

export default UpperPanel;