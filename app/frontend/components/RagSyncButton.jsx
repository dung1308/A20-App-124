import React, { useState } from 'react';
import api from '../services/api';
import { toast } from 'react-hot-toast';

/**
 * RagSyncButton Component
 * -----------------------
 * Triggers the manual RAG data synchronization and displays the report.
 * Assumes the presence of a JWT token in localStorage for Admin authentication.
 */
const RagSyncButton = () => {
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState('');
  const [progress, setProgress] = useState(0);
  const [statusMessage, setStatusMsg] = useState('');

  const handleSync = async () => {
    setLoading(true);
    setError(null);
    setReport(null);
    setSuccessMsg('');
    setProgress(0);
    setStatusMsg('Đang khởi tạo kết nối...');

    try {
      await api.streamRagIngest((data) => {
        if (data.error) throw new Error(data.error);

        setProgress(data.progress || 0);
        setStatusMsg(data.message || '');
        if (data.report) setReport(data.report);
        if (data.done) {
          setSuccessMsg("Đồng bộ hóa hoàn tất!");
          toast.success("Hệ thống tri thức đã được cập nhật.");
        }
      });
    } catch (err) {
      console.error('RAG Sync error:', err);
      const msg = err.response?.data?.detail || 'Đồng bộ hóa thất bại. Vui lòng kiểm tra quyền hạn.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm">
      <div className="flex items-center gap-3 mb-4">
        <div className="p-2 bg-blue-50 rounded-xl text-primary">
          <span className="material-symbols-outlined text-2xl">sync_saved_locally</span>
        </div>
        <div>
          <h3 className="text-sm font-black text-slate-800 uppercase tracking-wider">Cập nhật tri thức AI</h3>
          <p className="text-[10px] text-slate-500 font-bold uppercase tracking-tight">Cơ chế nạp: Daily (Mỗi 24h)</p>
        </div>
      </div>
      
      <p className="text-xs text-slate-600 mb-6 leading-relaxed">
        Làm mới cơ sở dữ liệu Vector từ các tệp nguồn Admissions và FAQ. AI sẽ tự động đồng bộ hàng ngày, nhưng bạn có thể kích hoạt thủ công nếu vừa cập nhật dữ liệu.
      </p>

      {loading && (
        <div className="mb-6 space-y-2 animate-in fade-in duration-300">
          <div className="flex justify-between items-end">
            <p className="text-[10px] font-black text-primary uppercase tracking-tighter">{statusMessage}</p>
            <p className="text-[10px] font-mono font-bold text-slate-400">{progress}%</p>
          </div>
          <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
            <div 
              className="h-full bg-primary transition-all duration-500 ease-out shadow-[0_0_8px_rgba(0,52,102,0.3)]" 
              style={{ width: `${progress}%` }}
            ></div>
          </div>
        </div>
      )}

      <div className="space-y-4">
        <button
          onClick={handleSync}
          disabled={loading}
          className={`w-full py-3 rounded-xl text-xs font-black uppercase tracking-widest transition-all flex items-center justify-center gap-2 ${
            loading ? 'bg-slate-100 text-slate-400' : 'bg-primary text-white hover:shadow-lg active:scale-95'
          }`}
        >
          <span className={`material-symbols-outlined text-lg ${loading ? 'animate-spin' : ''}`}>
            {loading ? 'sync' : 'database_sync'}
          </span>
          {loading ? 'Đang nạp dữ liệu...' : 'Nạp dữ liệu ngay'}
        </button>

        {report && (
          <div className="p-4 bg-emerald-50 border border-emerald-100 rounded-2xl animate-in fade-in zoom-in duration-300">
            <p className="text-[10px] font-black text-emerald-700 uppercase tracking-widest mb-3 flex items-center gap-2">
              <span className="material-symbols-outlined text-sm">check_circle</span>
              Báo cáo đồng bộ
            </p>
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-white/60 p-2 rounded-lg"><p className="text-[9px] text-slate-400 font-bold uppercase">FAQ mới</p><p className="text-sm font-black text-emerald-600">{report.faq_added}</p></div>
              <div className="bg-white/60 p-2 rounded-lg"><p className="text-[9px] text-slate-400 font-bold uppercase">FAQ cập nhật</p><p className="text-sm font-black text-blue-600">{report.faq_updated}</p></div>
              <div className="bg-white/60 p-2 rounded-lg"><p className="text-[9px] text-slate-400 font-bold uppercase">Tuyển sinh mới</p><p className="text-sm font-black text-emerald-600">{report.admissions_added}</p></div>
              <div className="bg-white/60 p-2 rounded-lg"><p className="text-[9px] text-slate-400 font-bold uppercase">Tuyển sinh cập nhật</p><p className="text-sm font-black text-blue-600">{report.admissions_updated}</p></div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default RagSyncButton;
