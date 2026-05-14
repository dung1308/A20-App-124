import { useState, useCallback, useEffect } from 'react';
import api from '../services/api';
import { useStore } from '../state/store';

const fallbackReasonFromResponse = (res) => {
  if (res.status === 'rejected') return 'judge_rejected';
  if (res.fallback) return 'backend_fallback';
  if (typeof res.response === 'string' && res.response.toLowerCase().includes('hồ sơ')) return 'missing_profile';
  return null;
};

const fallbackReasonFromError = (err) => {
  if (err.response?.status === 429) return 'rate_limit';
  if (err.response?.status === 400) return 'guardrail_blocked';
  if (err.name === 'CanceledError') return 'cancelled';
  return 'model_or_network_error';
};

const shouldSuggestWizard = (userId, text, res) => {
  if (!userId || localStorage.getItem(`wizard_completed_${userId}`) === 'true') return false;
  if ((res.recommendations || []).length > 0) return false;

  const normalized = text.toLowerCase();
  return ['ngành', 'chon', 'chọn', 'phù hợp', 'phu hop', 'tư vấn', 'tu van', 'hướng nghiệp'].some((keyword) =>
    normalized.includes(keyword)
  );
};

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

      const wizardHint = shouldSuggestWizard(userId, text, res)
        ? "\n\nNếu bạn muốn AI chọn Top 3 ngành sát với sở thích của mình hơn, hãy mở mục Wizard trong thanh bên hoặc vào Profile và bấm “Làm Wizard”."
        : "";

      const assistantMsg = {
        role: 'assistant',
        content: `${res.response || "Xin lỗi, tôi không nhận được phản hồi."}${wizardHint}`,
        sources: res.sources,
        references: res.references,
        data: res.recommendations,
        type: res.recommendations.length > 0 ? 'recommendation' : 'text',
        fallback: res.fallback || false,
        fallbackReason: fallbackReasonFromResponse(res),
        intent: res.intent,
        status: res.status,
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, assistantMsg]);

      // Handle session handoff/updates if the backend provides a new session ID
      const newSid = res.sessionId;
      const sessionTitle = res.sessionTitle;

      // Update session state if ID changed or a new title was generated (e.g. auto-rename)
      if (onSessionUpdate && ((newSid && newSid !== sessionId) || sessionTitle)) {
        onSessionUpdate(newSid || sessionId, sessionTitle);
      }
    } catch (err) {
      if (err.name !== 'CanceledError') {
        console.error("Chat Error:", err);
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: err.response?.status === 429
            ? "Bạn đang gửi yêu cầu quá nhanh. Vui lòng đợi một chút rồi thử lại."
            : "Lỗi kết nối máy chủ. Vui lòng thử lại sau.",
          fallback: true,
          fallbackReason: fallbackReasonFromError(err),
          status: 'error',
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
