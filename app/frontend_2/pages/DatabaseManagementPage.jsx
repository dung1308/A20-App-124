import React, { useState, useEffect } from 'react';
import api from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';

/**
 * DatabaseManagementPage Component
 * Fetches and displays real-time database status from the backend.
 */
const DatabaseManagementPage = () => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await api.get('/api/system/db-status');
        setStatus(response.data);
      } catch (err) {
        setError(err.response?.data?.detail || "Không thể truy cập thông tin hệ thống.");
      } finally {
        setLoading(false);
      }
    };
    fetchStatus();
  }, []);

  if (loading) return <LoadingSpinner fullPage />;

  return (
    <div className="p-8 h-full overflow-y-auto">
      <div className="max-w-4xl mx-auto bg-white p-8 rounded-2xl shadow-sm border border-slate-200">
        <h1 className="text-3xl font-bold text-gray-800 mb-4">Database Management</h1>
        
        {error ? (
          <div className="bg-red-50 text-red-700 p-4 rounded-xl border border-red-100">
            {error}
          </div>
        ) : (
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 bg-slate-50 rounded-xl">
                <p className="text-xs font-bold text-slate-400 uppercase">Trạng thái</p>
                <p className={`text-lg font-bold ${status.status === 'connected' ? 'text-green-600' : 'text-red-600'}`}>
                  {status.status === 'connected' ? 'Đã kết nối' : 'Mất kết nối'}
                </p>
              </div>
              <div className="p-4 bg-slate-50 rounded-xl">
                <p className="text-xs font-bold text-slate-400 uppercase">Cơ sở dữ liệu</p>
                <p className="text-lg font-bold text-slate-800">{status.database} ({status.type})</p>
              </div>
            </div>
            <div>
              <p className="text-xs font-bold text-slate-400 uppercase mb-2">Bảng hiện có</p>
              <div className="flex flex-wrap gap-2">
                {status.tables.map(table => (
                  <span key={table} className="px-3 py-1 bg-blue-50 text-blue-700 rounded-lg text-sm font-medium border border-blue-100">{table}</span>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DatabaseManagementPage;