import React from 'react';

const Step1 = ({ data, onUpdate }) => {
  const options = ["Công nghệ", "Kinh doanh", "Nghệ thuật", "Khoa học Xã hội"];

  const toggleOption = (option) => {
    const newData = data.includes(option)
      ? data.filter((item) => item !== option)
      : [...data, option];
    onUpdate({ interests: newData });
  };

  return (
    <div className="flex flex-col gap-3">
      <h3 className="text-lg font-bold text-blue-900 mb-4 text-left">Bạn thích lĩnh vực nào?</h3>
      {options.map((option) => (
        <button
          key={option}
          onClick={() => toggleOption(option)}
          className={`w-full p-4 text-left border-2 rounded-xl font-semibold transition-all duration-200 ${
            data.includes(option)
              ? "border-blue-900 bg-blue-50 text-blue-900 shadow-md"
              : "border-slate-200 text-slate-600 hover:border-blue-300"
          }`}
        >
          {option}
        </button>
      ))}
    </div>
  );
};

export default Step1;