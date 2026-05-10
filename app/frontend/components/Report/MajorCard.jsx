import React from 'react';

const MajorCard = ({ major }) => {
  const getScoreColor = (score) => {
    if (score >= 70) return 'text-emerald-600 bg-emerald-50 border-emerald-100';
    if (score >= 40) return 'text-amber-600 bg-amber-50 border-amber-100';
    return 'text-red-600 bg-red-50 border-red-100';
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm hover:shadow-md transition-all duration-300">
      <div className="flex justify-between items-start mb-4">
        <h3 className="text-lg font-bold text-blue-900 leading-tight">{major.major_name}</h3>
        <span className={`px-2 py-1 rounded text-[10px] font-black uppercase tracking-wider border ${getScoreColor(major.match_score)}`}>
          {major.match_score}% Match
        </span>
      </div>
      <div className="space-y-4">
        <p className="text-sm text-slate-600 leading-relaxed"><strong className="text-slate-800">Tại sao phù hợp:</strong> {major.match_reason}</p>
        <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
          <p className="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-1">Sinh viên VinUni học gì?</p>
          <p className="text-xs text-slate-500 leading-relaxed italic">{major.what_students_do}</p>
        </div>
      </div>
    </div>
  );
};

export default MajorCard;