import React from 'react';

const Step4 = ({ data, onUpdate }) => {
  const options = [
    { id: 'solo', label: 'Làm việc độc lập' },
    { id: 'team', label: 'Làm việc nhóm' },
    { id: 'mixed', label: 'Linh hoạt cả hai' }
  ];

  return (
    <div className="flex flex-col gap-3">
      <h3 className="text-lg font-bold text-blue-900 mb-4 text-left">Phong cách làm việc của bạn?</h3>
      {options.map((option) => (
        <button
          key={option.id}
          onClick={() => onUpdate({ work_style: option.id })}
          className={`w-full p-4 text-left border-2 rounded-xl font-semibold transition-all duration-200 ${
            data === option.id
              ? "border-blue-900 bg-blue-50 text-blue-900 shadow-md"
              : "border-slate-200 text-slate-600 hover:border-blue-300"
          }`}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
};

export default Step4;