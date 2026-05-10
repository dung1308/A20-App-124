import React, { useState, useEffect } from 'react';
import api from '../../services/api';

const SessionSidebar = ({ userId, activeSessionId, onSelectSession, refreshTrigger }) => {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchSessions = async () => {
    if (!userId) return;
    setLoading(true);
    try {
      const data = await api.getSessions(userId);
      setSessions(data.sessions || []);
    } catch (error) {
      console.error("Error fetching sessions:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSessions();
  }, [userId, refreshTrigger]);

  const handleDelete = async (e, sessionId) => {
    e.stopPropagation();
    if (!window.confirm("Bạn có chắc chắn muốn xóa phiên hội thoại này?")) return;
    try {
      await api.deleteSession(sessionId);
      setSessions(sessions.filter(s => s.id !== sessionId));
      if (activeSessionId === sessionId) {
        onSelectSession('new');
      }
    } catch (error) {
      alert("Không thể xóa phiên hội thoại.");
    }
  };

  return (
    <div className="w-64 bg-slate-900 h-full flex flex-col text-slate-300 border-r border-slate-800">
      <div className="p-4">
        <button 
          onClick={() => onSelectSession('new')}
          className="w-full flex items-center gap-3 px-4 py-3 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg transition-all text-sm font-medium text-white"
        >
          <span className="material-symbols-outlined text-sm">add</span>
          Cuộc trò chuyện mới
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-2 space-y-1">
        <p className="px-4 py-2 text-[10px] uppercase tracking-wider font-bold text-slate-500">Lịch sử trò chuyện</p>
        
        {loading ? (
          <div className="px-4 py-2 text-xs animate-pulse">Đang tải...</div>
        ) : sessions.length === 0 ? (
          <div className="px-4 py-2 text-xs text-slate-600 italic">Chưa có hội thoại nào</div>
        ) : (
          sessions.map((session) => (
            <div 
              key={session.id}
              onClick={() => onSelectSession(session.id)}
              className={`group flex items-center gap-3 px-4 py-3 rounded-lg cursor-pointer transition-all relative ${
                activeSessionId === session.id 
                  ? 'bg-slate-800 text-white' 
                  : 'hover:bg-slate-800/50'
              }`}
            >
              <span className="material-symbols-outlined text-lg opacity-50">chat_bubble</span>
              <div className="flex-1 overflow-hidden">
                <p className="text-sm truncate pr-6">
                  {session.title || "Hội thoại mới"}
                </p>
                <p className="text-[10px] opacity-40">
                  {new Date(session.created_at).toLocaleDateString('vi-VN')}
                </p>
              </div>
              
              <button 
                onClick={(e) => handleDelete(e, session.id)}
                className="absolute right-2 opacity-0 group-hover:opacity-100 hover:text-red-400 p-1 rounded transition-all"
              >
                <span className="material-symbols-outlined text-sm">delete</span>
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default SessionSidebar;