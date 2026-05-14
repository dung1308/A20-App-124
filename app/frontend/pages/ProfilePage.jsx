import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import CVUpload from '../components/CVUpload/CVUpload';
import api from '../services/api';

const ProfilePage = () => {
  const navigate = useNavigate();
  const userEmail = localStorage.getItem('user_email');
  const [profile, setProfile] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState({
    full_name: '',
    phone: '',
    gpa: '',
    ielts: '',
    majors: ''
  });

  const hasWizardAnswers = Boolean(
    (profile?.interests || []).length > 0 &&
    (profile?.strengths || []).length > 0 &&
    (profile?.dislikes || []).length > 0 &&
    profile?.work_style
  );

  const fetchProfile = async () => {
    setLoading(true);
    try {
      const data = await api.getProfile(userEmail);
      setProfile(data);
      setFormData({
        full_name: data.full_name || '',
        phone: data.phone || '',
        gpa: data.gpa || '',
        ielts: (data.test_scores || {}).ielts || '',
        majors: (data.preferred_majors || []).join(', ')
      });
    } catch (err) {
      toast.error('Không thể tải thông tin hồ sơ.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfile();
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.updateProfile(userEmail, {
        full_name: formData.full_name,
        phone: formData.phone,
        gpa: formData.gpa === '' ? null : parseFloat(formData.gpa),
        test_scores: { ielts: formData.ielts },
        preferred_majors: formData.majors.split(',').map((m) => m.trim()).filter(Boolean)
      });
      toast.success('Hồ sơ đã được cập nhật thành công.');
      setIsEditing(false);
      fetchProfile();
    } catch (err) {
      toast.error('Lỗi khi cập nhật hồ sơ.');
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    if (!window.confirm('Bạn có chắc chắn muốn hủy? Mọi thay đổi chưa lưu sẽ bị mất.')) return;
    setIsEditing(false);
    if (profile) {
      setFormData({
        full_name: profile.full_name || '',
        phone: profile.phone || '',
        gpa: profile.gpa || '',
        ielts: (profile.test_scores || {}).ielts || '',
        majors: (profile.preferred_majors || []).join(', ')
      });
    }
  };

  const handleViewCV = async () => {
    try {
      const response = await api.downloadCV(userEmail);
      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
      window.open(url, '_blank', 'noopener,noreferrer');
      setTimeout(() => window.URL.revokeObjectURL(url), 60000);
    } catch (err) {
      toast.error('Không thể mở CV. Vui lòng tải lại file PDF.');
    }
  };

  if (loading) {
    return <div className="p-12 text-center text-slate-400 font-medium animate-pulse">Đang tải hồ sơ...</div>;
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-10 h-full overflow-y-auto scrollbar-thin scrollbar-thumb-slate-200 scrollbar-track-transparent">
      <header className="border-b-4 border-primary pb-4 mb-8">
        <h2 className="text-3xl font-black text-primary m-0 tracking-tight">Hồ sơ cá nhân</h2>
        <p className="text-slate-500 font-medium mt-1">Quản lý thông tin để Trợ lý AI có thể tư vấn hướng nghiệp chính xác nhất cho bạn.</p>
      </header>

      <div className="bg-blue-50/50 border border-blue-100 rounded-2xl p-5 mb-8 flex items-center gap-4">
        <div className="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 shadow-sm border border-blue-200">
          <span className="material-symbols-outlined text-2xl" style={{ fontVariationSettings: "'FILL' 1" }}>verified_user</span>
        </div>
        <div>
          <p className="text-sm font-black text-blue-900">Dữ liệu được bảo mật</p>
          <p className="text-xs text-blue-700 font-medium">Thông tin của bạn chỉ được sử dụng cho mục đích tư vấn tuyển sinh tại VinUni.</p>
        </div>
      </div>

      <div className="bg-white border border-amber-200 rounded-2xl p-5 mb-8 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-sm">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 rounded-xl bg-amber-50 flex items-center justify-center text-amber-600 border border-amber-100">
            <span className="material-symbols-outlined text-2xl">route</span>
          </div>
          <div>
            <p className="text-sm font-black text-slate-900">
              {hasWizardAnswers ? 'Wizard chọn ngành đã có dữ liệu' : 'Bạn chưa hoàn thành Wizard chọn ngành'}
            </p>
            <p className="text-xs text-slate-500 font-medium mt-1">
              {hasWizardAnswers
                ? 'Bạn có thể làm lại Wizard bất cứ lúc nào để thay đổi câu trả lời và cập nhật gợi ý ngành.'
                : 'Trả lời 4 bước ngắn để AI có đủ sở thích, thế mạnh và phong cách làm việc trước khi tư vấn ngành.'}
            </p>
          </div>
        </div>
        <button
          onClick={() => navigate('/wizard')}
          className="px-5 py-3 bg-primary text-white rounded-xl text-xs font-black uppercase tracking-widest hover:shadow-lg active:scale-95 transition-all flex items-center justify-center gap-2 shrink-0"
        >
          <span className="material-symbols-outlined text-[18px]">psychology_alt</span>
          {hasWizardAnswers ? 'Làm lại Wizard' : 'Làm Wizard'}
        </button>
      </div>

      <div className="bg-white border border-slate-200 rounded-3xl shadow-xl shadow-blue-900/5 overflow-hidden">
        <div className="p-8 space-y-8">
          <section>
            <h3 className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-6 border-b border-slate-50 pb-2">Thông tin cơ bản</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Field label="Họ và tên" editing={isEditing}>
                {isEditing ? (
                  <input className={inputClass} value={formData.full_name} onChange={(e) => setFormData({ ...formData, full_name: e.target.value })} placeholder="Nguyễn Văn A" />
                ) : (
                  <DisplayValue>{profile?.full_name || 'Chưa cập nhật'}</DisplayValue>
                )}
              </Field>
              <Field label="Email liên hệ">
                <DisplayValue muted>{userEmail}</DisplayValue>
              </Field>
            </div>
          </section>

          <section>
            <h3 className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-6 border-b border-slate-50 pb-2">Năng lực học thuật</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Field label="GPA mục tiêu/hiện tại" editing={isEditing}>
                {isEditing ? (
                  <input type="number" step="0.1" className={inputClass} value={formData.gpa} onChange={(e) => setFormData({ ...formData, gpa: e.target.value })} placeholder="VD: 3.8" />
                ) : (
                  <DisplayValue icon="grade">{profile?.gpa || 'Chưa cập nhật'}</DisplayValue>
                )}
              </Field>
              <Field label="IELTS/TOEFL" editing={isEditing}>
                {isEditing ? (
                  <input className={inputClass} value={formData.ielts} onChange={(e) => setFormData({ ...formData, ielts: e.target.value })} placeholder="VD: IELTS 7.5" />
                ) : (
                  <DisplayValue icon="language">{(profile?.test_scores || {}).ielts || 'Chưa có'}</DisplayValue>
                )}
              </Field>
            </div>
          </section>

          <section>
            <h3 className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-6 border-b border-slate-50 pb-2">Nguyện vọng ngành học</h3>
            <Field label="Các ngành quan tâm" editing={isEditing}>
              {isEditing ? (
                <input className={inputClass} value={formData.majors} onChange={(e) => setFormData({ ...formData, majors: e.target.value })} placeholder="Ví dụ: cs, ba, ee..." />
              ) : (
                <div className="flex flex-wrap gap-2 pt-1">
                  {(profile?.preferred_majors || []).length > 0 ? (
                    profile.preferred_majors.map((major) => (
                      <span key={major} className="px-4 py-1.5 bg-blue-900 text-white rounded-lg text-[11px] font-black uppercase tracking-wider shadow-sm">{major}</span>
                    ))
                  ) : (
                    <p className="text-slate-400 text-sm italic font-medium px-1">Chưa chọn ngành quan tâm</p>
                  )}
                </div>
              )}
            </Field>
          </section>

          <section>
            <h3 className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-6 border-b border-slate-50 pb-2">CV của tôi</h3>
            <div className="flex flex-col gap-4">
              {profile?.cv_url ? (
                <div className="flex items-center gap-4 p-4 bg-slate-50 rounded-xl border border-slate-200">
                  <div className="w-10 h-10 rounded-lg bg-red-50 flex items-center justify-center text-red-600">
                    <span className="material-symbols-outlined text-2xl">picture_as_pdf</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-bold text-slate-900 truncate">{profile.cv_filename || 'Hồ sơ năng lực (CV)'}</p>
                    <p className="text-[10px] text-slate-500 font-black uppercase tracking-tighter">
                      {profile.cv_uploaded_at ? `Đã tải lên ${new Date(profile.cv_uploaded_at).toLocaleDateString('vi-VN')}` : 'Đã tải lên hệ thống'}
                    </p>
                  </div>
                  <button type="button" onClick={handleViewCV} className="px-4 py-2 bg-white border border-slate-200 rounded-lg text-xs font-black text-primary hover:bg-slate-100 transition-all shadow-sm flex items-center gap-2">
                    <span className="material-symbols-outlined text-sm">visibility</span>
                    Xem PDF
                  </button>
                </div>
              ) : (
                <p className="text-slate-400 text-sm italic font-medium px-1">Bạn chưa tải lên CV nào.</p>
              )}

              {isEditing && (
                <div className="p-4 bg-slate-50 rounded-2xl border-2 border-dashed border-slate-200 hover:border-primary/30 transition-colors">
                  <CVUpload
                    onUploadSuccess={() => {
                      toast.success('CV đã được lưu vào hồ sơ.');
                      fetchProfile();
                    }}
                  />
                </div>
              )}
            </div>
          </section>
        </div>

        <div className="p-8 bg-slate-50 border-t border-slate-100 flex justify-end gap-4">
          {isEditing ? (
            <>
              <button onClick={handleCancel} className="px-6 py-3 text-slate-500 text-sm font-black uppercase tracking-widest hover:text-slate-800 transition-colors">Hủy</button>
              <button onClick={handleSave} disabled={saving} className="px-8 py-3 bg-primary text-white font-black text-sm uppercase tracking-widest rounded-xl hover:shadow-lg active:scale-95 transition-all shadow-md disabled:opacity-50">
                {saving ? 'Đang lưu...' : 'Lưu thay đổi'}
              </button>
            </>
          ) : (
            <button onClick={() => setIsEditing(true)} className="px-8 py-3 bg-white border-2 border-primary text-primary font-black text-sm uppercase tracking-widest rounded-xl hover:bg-primary/5 active:scale-95 transition-all">
              Chỉnh sửa hồ sơ
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

const inputClass = 'w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-4 focus:ring-primary/5 focus:border-primary transition-all text-sm font-medium';

const Field = ({ label, children }) => (
  <div className="flex flex-col gap-2">
    <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">{label}</label>
    {children}
  </div>
);

const DisplayValue = ({ children, icon, muted = false }) => (
  <div className={`px-4 py-3 rounded-xl border border-transparent flex items-center gap-2 ${muted ? 'bg-slate-100/50 text-slate-500' : 'bg-slate-50/50 text-slate-900'}`}>
    {icon && <span className="material-symbols-outlined text-blue-600 text-[18px]">{icon}</span>}
    <p className="font-bold text-sm">{children}</p>
  </div>
);

export default ProfilePage;
