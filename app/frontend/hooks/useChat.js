import { useState, useCallback, useEffect } from 'react';
import api from '../services/api';
import { useStore } from '../state/store';

export const useChat = (userId, sessionId, onSessionUpdate) => {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [abortController, setAbortController] = useState(null);

  // Retrieve CV signals from the global store to provide context to the LLM
  const { cvSignals } = useStore();

  // Load history when session changes or on mount
  useEffect(() => {
    const loadHistory = async () => {
      if (!sessionId || sessionId === 'new') {
        setMessages([]);
        return;
      }
      try {
        const res = await api.getSessionMessages(sessionId);
        if (res.status === 'success') {
          setMessages(res.messages);
        }
      } catch (err) {
        console.error("Failed to load history:", err);
      }
    };
    loadHistory();
  }, [sessionId]);

  const sendMessage = useCallback(async (text) => {
    if (!text.trim()) return;

    const userMsg = { 
      role: 'user', 
      content: text, 
      timestamp: new Date().toISOString() 
    };
    
    setMessages(prev => [...prev, userMsg]);
    setLoading(true);

    const controller = new AbortController();
    setAbortController(controller);

    try {
      const payload = {
        userId,
        sessionId,
        text,
        history: messages.map(m => ({ role: m.role, content: m.content })),
        persona_summary: cvSignals?.persona_summary
      };

      const res = await api.postChat(payload, { signal: controller.signal });

      // MAPPING: Ensure the 'answer' field from the backend JSON is mapped to the 'content' property
      const assistantMsg = {
        role: 'assistant',
        content: res.answer || res.response || "Xin lỗi, tôi không nhận được phản hồi.",
        data: res.major || res.top3 || [],
        type: (res.major || (res.top3 && res.top3.length > 0)) ? 'recommendation' : 'text',
        fallback: res.fallback || false,
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, assistantMsg]);

      // Handle session handoff/updates if the backend provides a new session ID
      const newSid = res.sessionId || res.session_id;
      if (newSid && newSid !== sessionId && onSessionUpdate) {
        onSessionUpdate(newSid);
      }
    } catch (err) {
      if (err.name !== 'CanceledError') {
        console.error("Chat Error:", err);
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: "Lỗi kết nối máy chủ. Vui lòng thử lại sau.",
          timestamp: new Date().toISOString()
        }]);
      }
    } finally {
      setLoading(false);
      setAbortController(null);
    }
  }, [userId, sessionId, messages, onSessionUpdate]);

  const stopGenerating = () => {
    if (abortController) {
      abortController.abort();
    }
  };

  return { messages, setMessages, sendMessage, stopGenerating, loading };
};