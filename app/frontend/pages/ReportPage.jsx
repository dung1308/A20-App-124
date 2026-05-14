import React, { useState } from 'react';
import { useStore } from '../state/store';
import { Link } from 'react-router-dom';
import MajorCard from '../components/Report/MajorCard';
import LoadingSpinner from '../components/LoadingSpinner';
import { useAuth } from '../context/AuthContext'; // Import useAuth
import ChatBox from '../components/Chat/ChatBox'; // Assuming ChatBox also needs userId
import api from '../services/api';
import { toast } from 'react-hot-toast';

const ReportPage = () => {
  const { matchResults } = useStore();
  const { userId, isAuthenticated } = useAuth(); // Get userId and isAuthenticated from AuthContext
  const [showChat, setShowChat] = useState(false);

  const handleConsultationClick = async () => {
    try {
      await api.logConsultationClick('report');
      toast.success('Đã ghi nhận nhu cầu tư vấn. Chuyên viên sẽ có dữ liệu để hỗ trợ bạn.');
    } catch (err) {
      toast.error('Không thể ghi nhận yêu cầu tư vấn lúc này.');
    }
  };

  if (!matchResults) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-8">
        <div className="text-center p-8 h-full overflow-y-auto">
          <LoadingSpinner size="lg" className="mb-4" timeoutMessage="Kết quả phân tích đang được tạo. Quá trình này có thể mất vài phút." />
          <p className="text-slate-600 font-medium">Đang tải kết quả phân tích...</p>
          <Link to="/wizard" className="text-blue-700 text-sm mt-4 inline-block underline">Quay lại khảo sát</Link>
        </div>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated || !userId) {
    return <div className="p-8 text-red-500 text-center">Bạn cần đăng nhập để xem báo cáo.</div>;
  }

  return (
    <div className="p-8 h-full overflow-y-auto">
      <div className="max-w-5xl mx-auto">
        <main>
            <div className="bg-blue-900 text-white p-8 rounded-3xl mb-8 relative overflow-hidden shadow-xl shadow-blue-900/20">
              <div className="relative z-10">
                <h2 className="text-3xl font-bold mb-2">Kết quả của bạn</h2>
                <p className="text-blue-100 opacity-80 text-sm italic">{matchResults.disclaimer}</p>
              </div>
              <div className="absolute top-0 right-0 w-64 h-64 bg-blue-800 rounded-full -mr-20 -mt-20 opacity-50"></div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
              {(matchResults.top3 || []).map((major) => (
                <MajorCard key={major.major_id} major={major} />
              ))}
            </div>

            {matchResults.fallback && (
              <div className="bg-amber-50 border border-amber-200 p-6 rounded-2xl mb-12">
                <p className="text-amber-800 font-bold flex items-center gap-2 mb-1">
                  <span className="material-symbols-outlined">info</span>
                  AI chưa tìm thấy ngành phù hợp hoàn hảo
                </p>
                <p className="text-amber-700 text-sm">Hãy thử trò chuyện với cố vấn bên dưới để cung cấp thêm thông tin hoặc giải đáp thắc mắc.</p>
              </div>
            )}

            {matchResults.fallback && (
              <button
                onClick={handleConsultationClick}
                className="mb-8 px-5 py-2.5 bg-amber-600 text-white rounded-xl text-xs font-black uppercase tracking-widest hover:bg-amber-700 transition-colors"
              >
                Đăng ký gặp tư vấn viên
              </button>
            )}

            <section className="bg-white rounded-3xl p-8 border border-slate-200 shadow-sm mb-20">
              {!showChat ? (
                <div className="text-center py-6">
                  <h3 className="text-xl font-bold text-blue-900 mb-2">Bạn muốn tìm hiểu thêm?</h3>
                  <p className="text-slate-500 mb-8">Hãy trò chuyện với cố vấn AI để giải đáp các thắc mắc về ngành học và lộ trình sự nghiệp.</p>
                  <button className="px-8 py-3 bg-[#fed65b] text-[#745c00] rounded-xl font-bold shadow-lg hover:shadow-xl transition-all active:scale-95" onClick={() => setShowChat(true)}>
                    Hỏi thêm câu hỏi
                  </button>
                  <button
                    className="ml-3 px-8 py-3 bg-white border border-blue-900 text-blue-900 rounded-xl font-bold shadow-sm hover:bg-blue-50 transition-all active:scale-95"
                    onClick={handleConsultationClick}
                  >
                    Đăng ký tư vấn chuyên sâu
                  </button>
                </div>
              ) : (
                <ChatBox userId={userId} />
              )}
            </section>
        </main>
      </div>
    </div>
  );
};

export default ReportPage;
