import React, { useState } from 'react';
import { useStore } from '../../state/store';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';

const CVUpload = () => {
  const { setCVSignals, setCVText, cvSignals } = useStore();
  const { userId } = useAuth();
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState('idle'); // idle | uploading | success | error
  const [errorMsg, setErrorMsg] = useState('');

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
      if (!allowedTypes.includes(selectedFile.type)) {
        setErrorMsg('Vui lòng chọn file PDF, DOCX hoặc TXT.');
        setFile(null);
        return;
      }
      setErrorMsg('');
      setFile(selectedFile);
      setStatus('idle');
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    
    setStatus('uploading');
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await api.post(`/api/upload-cv?user_id=${userId}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      setCVSignals(response.data);
      setStatus('success');
    } catch (error) {
      console.error("CV Upload failed:", error);
      setStatus('error');
      setErrorMsg('Không thể xử lý CV. Vui lòng thử lại.');
    }
  };

  const handleRemove = () => {
    setCVSignals(null);
    setCVText('');
    setFile(null);
    setStatus('idle');
  };

  return (
    <div className="cv-upload-container bg-blue-50/50 p-6 rounded-2xl border border-blue-100">
      <h3 className="text-lg font-bold text-blue-900 mb-1">Tải lên CV (Tùy chọn)</h3>
      <p className="text-sm text-slate-600 mb-1">We use your CV to improve recommendations.</p>
      <p className="text-xs text-slate-500 mb-6 italic">Hệ thống sẽ phân tích kỹ năng và kinh nghiệm của bạn để đưa ra gợi ý chính xác hơn.</p>
      
      <div className="upload-controls flex flex-col gap-4">
        <input 
          type="file" 
          accept=".pdf,.docx,.txt" 
          onChange={handleFileChange} 
          disabled={status === 'uploading'}
          className="block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-900 file:text-white hover:file:bg-blue-800 transition-all cursor-pointer"
        />
        {!cvSignals ? (
          <button 
            onClick={handleUpload} 
            disabled={!file || status === 'uploading'}
            className="px-6 py-2.5 bg-fed65b text-745c00 rounded-lg font-bold text-sm shadow-sm hover:shadow-md disabled:opacity-50 disabled:cursor-not-allowed transition-all active:scale-95"
          >
            {status === 'uploading' ? 'Đang phân tích...' : 'Phân tích CV'}
          </button>
        ) : (
          <button onClick={handleRemove} className="px-6 py-2.5 border border-slate-300 text-slate-600 rounded-lg font-bold text-sm hover:bg-white transition-all">
            Gỡ bỏ CV
          </button>
        )}
      </div>

      {errorMsg && <p className="mt-3 text-xs text-red-600 font-medium flex items-center gap-1">❌ {errorMsg}</p>}
      {cvSignals && <p className="mt-3 text-xs text-green-700 font-medium flex items-center gap-1">✅ CV đang được sử dụng để tối ưu kết quả.</p>}
    </div>
  );
};

export default CVUpload;