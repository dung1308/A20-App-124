import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI.
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Log the error to your console or an error reporting service
    this.setState({ error, errorInfo });
    console.error("ErrorBoundary caught an error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      // You can render any custom fallback UI
      return (
        <div className="flex flex-col items-center justify-center p-12 m-4 bg-white border border-red-100 rounded-[24px] shadow-sm text-center">
          <div className="w-16 h-16 bg-red-50 rounded-full flex items-center justify-center mb-6">
            <span className="material-symbols-outlined text-red-600 text-3xl">warning</span>
          </div>
          <h2 className="text-2xl font-bold text-slate-900 mb-2">Đã xảy ra lỗi giao diện</h2>
          <p className="text-slate-500 mb-8 max-w-md">Một thành phần của ứng dụng gặp sự cố. Bạn có thể thử tải lại trang hoặc quay lại sau.</p>
          <button
            onClick={() => window.location.reload()}
            className="px-8 py-3 bg-[#003466] text-white font-bold rounded-xl hover:scale-[1.02] active:scale-95 transition-all shadow-lg shadow-blue-900/10"
          >
            Tải lại trang
          </button>
          
          {/* Chỉ hiển thị chi tiết lỗi khi đang ở môi trường phát triển */}
          {(import.meta.env.DEV || true) && this.state.error && (
            <div className="mt-12 w-full max-w-2xl text-left bg-slate-50 p-6 rounded-2xl border border-slate-200 overflow-auto">
              <p className="text-xs font-bold text-red-600 uppercase tracking-widest mb-3">Debug Info (Developer Only):</p>
              <pre className="text-xs font-mono text-slate-700 whitespace-pre-wrap">
                {this.state.error.toString()}
              </pre>
            </div>
          )}
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;