import React, { useState, useEffect } from 'react';

/**
 * LoadingSpinner Component
 * Một component spinner có thể tái sử dụng cho toàn bộ ứng dụng.
 * 
 * @param {string} size - 'sm' (nút bấm), 'md' (mặc định), 'lg' (trang báo cáo)
 * @param {string} color - 'blue' (màu thương hiệu), 'white' (dùng trong nút bấm), 'gray' (màu xám)
 * @param {boolean} fullPage - Nếu true, sẽ hiển thị một lớp phủ mờ toàn màn hình.
 * @param {number} timeoutDelay - Thời gian (ms) trước khi hiển thị thông báo timeout. Mặc định 5000ms (5s).
 * @param {string} timeoutMessage - Thông báo hiển thị khi timeout.
 * @param {string} className - Các class CSS bổ sung.
 */
const LoadingSpinner = ({ size = 'md', color = 'blue', fullPage = false, timeoutDelay = 5000, timeoutMessage = "Quá trình tải đang mất nhiều thời gian hơn dự kiến...", className = '' }) => {
  const [hasTimedOut, setHasTimedOut] = useState(false);
  const sizeClasses = {
    sm: 'w-4 h-4 border-2',
    md: 'w-8 h-8 border-[3px]',
    lg: 'w-12 h-12 border-4',
  };

  const colorClasses = {
    blue: 'border-[#003466]',
    white: 'border-white',
    gray: 'border-gray-400',
  };

  useEffect(() => {
    if (fullPage) {
      const timer = setTimeout(() => {
        setHasTimedOut(true);
      }, timeoutDelay);
      return () => clearTimeout(timer);
    }
    setHasTimedOut(false); // Reset if not fullPage or unmounted
  }, [fullPage, timeoutDelay]);

  const spinner = (
    <div
      className={`${sizeClasses[size]} ${colorClasses[color]} border-t-transparent rounded-full animate-spin`}
    />
  );

  if (fullPage) {
    return (
      <div className="fixed inset-0 bg-white/60 backdrop-blur-sm z-[9999] flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          {spinner}
          <span className="text-sm font-bold text-[#003466] uppercase tracking-widest">
            {hasTimedOut ? timeoutMessage : "Đang xử lý..."}
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className={`flex items-center justify-center ${className}`}>
      {spinner}
    </div>
  );
};

export default LoadingSpinner;