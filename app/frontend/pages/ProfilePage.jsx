import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api'; // Use the configured axios instance
import LoadingSpinner from '../components/LoadingSpinner';
import { useAuth } from '../context/AuthContext'; // Import from AuthContext
/**
 * ProfilePage Component
 * Displays the student's academic profile and preferences fetched via the CRM service.
 */
const ProfilePage = () => {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);
  const navigate = useNavigate();

  const { isAuthenticated, userId, token } = useAuth(); // Lấy isAuthenticated, userId và token từ AuthContext

  // State cho các trường thông tin mới
  const [fullName, setFullName] = useState('');
  const [dob, setDob] = useState('');
  const [phone, setPhone] = useState('');

  const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const response = await api.getProfile(userId);
        
        setProfile(response.data);
        // Khởi tạo giá trị cho form nếu có dữ liệu từ backend
        if (response.data) {
          setFullName(response.data.full_name || localStorage.getItem('user_name') || '');
          setDob(response.data.dob || '');
          setPhone(response.data.phone || '');
        }
      } catch (err) {
        console.error("Error fetching profile:", err);
        setError("Không thể tải thông tin hồ sơ. Vui lòng hoàn thành khảo sát tư vấn trước.");
      } finally {
        setLoading(false);
      }
    };

    if (isAuthenticated && userId && userId !== 'anonymous') { // Chỉ fetch nếu đã xác thực và có user_id hợp lệ
      fetchProfile();
    } else if (!isAuthenticated || !userId) {
      setError("Bạn cần đăng nhập để xem hồ sơ.");
      setLoading(false);
    }
  }, [userId, token]); // Thêm token vào dependency array

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.post(`/api/profile/${userId}`, {
        full_name: fullName,
        dob: dob,
        phone: phone
      });
      alert("Lưu thông tin thành công!");
      // Cập nhật lại tên hiển thị trong localStorage nếu cần
      localStorage.setItem('user_name', fullName);
    } catch (err) {
      console.error("Error saving profile:", err);
      alert("Lỗi khi lưu thông tin. Vui lòng thử lại.");
    } finally {
      setSaving(false);
    }
  };

  const handleDownloadCV = async () => {
    try {
      const response = await api.downloadCV(userId);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      // Đặt tên file mặc định hoặc lấy từ profile.cv_filename nếu có
      link.setAttribute('download', profile?.cv_filename || `CV_${userId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      alert("Không thể tải xuống CV. Có thể file đã bị xóa hoặc lỗi server.");
    }
  };

  if (loading) return <LoadingSpinner fullPage timeoutMessage="Hồ sơ đang được tải. Vui lòng đợi hoặc kiểm tra kết nối mạng." />;
  if (error) return <div className="p-8 text-red-500 text-center">{error}</div>;

  return (
    <div className="max-w-4xl mx-auto p-6">
      <header className="mb-8 border-b pb-4">
        <h1 className="text-3xl font-bold text-gray-800">Hồ sơ của tôi</h1>
        <p className="text-gray-600">Dữ liệu này giúp CRM Agent đưa ra những lời khuyên chính xác nhất cho bạn.</p>
      </header>

      <div className="mb-8 flex items-center gap-3 px-5 py-4 bg-emerald-50 border border-emerald-100 rounded-2xl shadow-sm animate-in fade-in slide-in-from-top-4 duration-700">
        <span className="material-symbols-outlined text-emerald-600 text-[22px]">verified_user</span>
        <p className="text-xs text-emerald-800 font-medium leading-relaxed">
          🛡️ Thông tin nhạy cảm của bạn (Email, SĐT) được mã hóa tự động trước khi gửi tới AI để đảm bảo an toàn tuyệt đối.
        </p>
      </div>

      {profile ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Personal Information Form */}
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 md:col-span-2">
            <h2 className="text-xl font-semibold mb-6 text-blue-700">Thông tin cá nhân</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-bold text-gray-500 uppercase">Họ và tên</label>
                <input 
                  type="text" 
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full p-3 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  placeholder="Nguyễn Văn A"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-bold text-gray-500 uppercase">Ngày sinh</label>
                <input 
                  type="date" 
                  value={dob}
                  onChange={(e) => setDob(e.target.value)}
                  className="w-full p-3 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-bold text-gray-500 uppercase">Số điện thoại</label>
                <input 
                  type="tel" 
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  className="w-full p-3 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  placeholder="09xx xxx xxx"
                />
              </div>
              <div className="flex items-end">
                <button 
                  onClick={handleSave}
                  disabled={saving}
                  className="w-full md:w-auto px-8 py-3 bg-blue-700 text-white font-bold rounded-lg hover:bg-blue-800 transition-all disabled:opacity-50"
                >
                  {saving ? "Đang lưu..." : "Lưu thay đổi"}
                </button>
              </div>
            </div>
          </div>

          {/* CV Management */}
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <h2 className="text-xl font-semibold mb-4 text-blue-700">CV & Hồ sơ</h2>
            {profile.cv_filename ? (
              <div className="flex flex-col gap-4">
                <div className="flex items-center gap-3 p-3 bg-blue-50 rounded-lg border border-blue-100">
                  <span className="material-symbols-outlined text-blue-600">description</span>
                  <div className="flex-1 overflow-hidden">
                    <p className="text-sm font-bold text-blue-900 truncate">{profile.cv_filename}</p>
                    <p className="text-[10px] text-blue-600 uppercase font-bold">Đã tải lên hệ thống AI</p>
                  </div>
                </div>
                <button
                  onClick={handleDownloadCV}
                  className="flex items-center justify-center gap-2 w-full py-2.5 bg-white border border-blue-200 text-blue-700 font-bold rounded-lg hover:bg-blue-50 transition-all text-sm shadow-sm"
                >
                  <span className="material-symbols-outlined text-lg">download</span>
                  Xem/Tải xuống CV
                </button>
              </div>
            ) : (
              <div className="text-center py-4">
                <p className="text-sm text-gray-400 italic mb-4">Bạn chưa tải lên CV nào.</p>
                <button
                  onClick={() => navigate('/wizard')}
                  className="text-sm text-blue-600 font-bold hover:underline"
                >
                  Tải lên tại Wizard ngay
                </button>
              </div>
            )}
          </div>

          {/* Academic Stats */}
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <h2 className="text-xl font-semibold mb-4 text-blue-700">Chỉ số học tập</h2>
            <div className="flex justify-between py-2 border-b">
              <span className="text-gray-500">GPA Mục tiêu/Hiện tại:</span>
              <span className="font-medium">{profile.gpa || 'Chưa cập nhật'}</span>
            </div>
            <div className="mt-4">
              <h3 className="text-sm font-bold text-gray-400 uppercase mb-2">Chứng chỉ ngoại ngữ</h3>
              {profile.test_scores ? (
                <ul className="space-y-1">
                  {Object.entries(profile.test_scores).map(([test, score]) => (
                    <li key={test} className="flex justify-between">
                      <span className="capitalize">{test}:</span>
                      <span className="font-medium text-green-600">{score}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-gray-400 italic">Chưa có thông tin điểm số.</p>
              )}
            </div>
          </div>

          {/* Major Preferences */}
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <h2 className="text-xl font-semibold mb-4 text-blue-700">Ngành học quan tâm</h2>
            {profile.preferred_majors && profile.preferred_majors.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {profile.preferred_majors.map((major) => (
                  <span key={major} className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm font-medium border border-blue-100">
                    {major}
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-gray-400 italic">Bạn chưa thực hiện khảo sát chọn ngành.</p>
            )}
          </div>

          {/* Extra Profile Data */}
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 md:col-span-2">
            <h2 className="text-xl font-semibold mb-4 text-blue-700">Chi tiết bổ sung</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {profile.profile_data ? Object.entries(profile.profile_data).map(([key, value]) => (
                <div key={key} className="p-3 bg-gray-50 rounded-lg">
                  <span className="block text-xs font-bold text-gray-400 uppercase">{key.replace(/_/g, ' ')}</span>
                  <span className="text-gray-800">
                    {Array.isArray(value) ? value.join(', ') : String(value)}
                  </span>
                </div>
              )) : (
                <p className="text-gray-400 italic">Không có dữ liệu mở rộng.</p>
              )}
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-yellow-50 p-6 rounded-lg border border-yellow-200 text-center">
          <p className="text-yellow-700">Hồ sơ của bạn hiện đang trống. Hãy bắt đầu bằng cách hoàn thành khảo sát tư vấn chọn ngành.</p>
        </div>
      )}
    </div>
  );
};

export default ProfilePage;