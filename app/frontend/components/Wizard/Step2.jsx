import React from 'react';

const Step2 = ({ data, onUpdate }) => {
  const options = ['Giải quyết vấn đề', 'Giao tiếp', 'Lãnh đạo', 'Sáng tạo', 'Phân tích dữ liệu'];
  
  const toggleOption = (opt) => {
    const next = data.includes(opt) 
      ? data.filter(i => i !== opt) 
      : [...data, opt];
    onUpdate({ strengths: next });
  };

  return (
    <div className="flex flex-col gap-3">
      <h2 className="text-lg font-bold text-blue-900 mb-4 text-left">Thế mạnh của bạn là gì?</h2>
      {options.map((opt) => (
        <button
          key={opt}
          onClick={() => toggleOption(opt)}
          className={`w-full p-4 text-left border-2 rounded-xl font-semibold transition-all duration-200 ${
            data.includes(opt)
              ? "border-blue-900 bg-blue-50 text-blue-900 shadow-md"
              : "border-slate-200 text-slate-600 hover:border-blue-300"
          }`}
        >
          {opt}
        </button>
      ))}
    </div>
  );
};
export default Step2;