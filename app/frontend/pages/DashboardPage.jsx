import React from 'react';
import { useNavigate } from 'react-router-dom';

const DashboardPage = () => {
  const navigate = useNavigate();

  return (
    <div className="p-8 h-full overflow-y-auto">
      <div className="max-w-4xl mx-auto">
        <h2 className="text-2xl font-bold mb-4 text-slate-800">Chào mừng trở lại!</h2>
        <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200">
          <p className="text-slate-600 mb-6 text-lg">Bạn đã hoàn thành khảo sát định hướng. Bây giờ, hãy trò chuyện với Cố vấn AI của chúng tôi để khám phá các lựa chọn tốt nhất dành cho bạn.</p>
          <button 
            onClick={() => navigate('/consultant')}
            className="px-8 py-4 bg-blue-700 text-white rounded-xl font-bold hover:bg-blue-800 transition-all transform active:scale-95 shadow-lg shadow-blue-200"
          >
            Bắt đầu tư vấn ngay
          </button>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;