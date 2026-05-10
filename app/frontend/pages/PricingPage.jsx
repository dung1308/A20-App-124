import React from 'react';

/**
 * PricingPage Component
 * A placeholder page for displaying pricing information.
 */
const PricingPage = () => {
  const plans = [
    {
      name: "Starter",
      price: "0",
      description: "Lý tưởng cho việc khám phá ban đầu.",
      features: [
        "Chưa có tính năng",
        "Khảo sát chọn ngành cơ bản",
        "5 câu hỏi với AI Mentor mỗi ngày",
        "Truy cập kho tài liệu chung",
        "Hỗ trợ qua Email"
      ],
      buttonText: "Bắt đầu miễn phí",
      highlight: false
    },
    {
      name: "Pro",
      price: "0",
      description: "Dành cho học sinh cần tư vấn chuyên sâu.",
      features: [
        "Chưa có tính năng",
        "Phân tích CV bằng AI",
        "Không giới hạn câu hỏi AI Mentor",
        "Báo cáo tiềm năng chi tiết",
        "Ưu tiên cập nhật thông tin mới nhất",
        "Lưu trữ lịch sử tư vấn trọn đời"
      ],
      buttonText: "Nâng cấp ngay",
      highlight: true
    },
    {
      name: "Elite",
      price: "Liên hệ",
      description: "Gói dành cho trường học & tổ chức.",
      features: [
        "Tất cả tính năng của gói Pro",
        "Cố vấn trực tiếp 1-1 (30p/tháng)",
        "Tài khoản quản lý dành cho GV",
        "Hỗ trợ 24/7 riêng biệt",
        "Tùy chỉnh lộ trình đào tạo"
      ],
      buttonText: "Liên hệ tư vấn",
      highlight: false
    }
  ];

  return (
    <div className="p-8 h-full overflow-y-auto bg-slate-50">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-black text-[#003466] mb-4">Gói dịch vụ tư vấn</h1>
          <p className="text-slate-600 max-w-2xl mx-auto">
            Chọn gói dịch vụ phù hợp để tối ưu hóa hành trình chinh phục cánh cửa đại học VinUni của bạn.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {plans.map((plan, index) => (
            <div 
              key={index} 
              className={`relative flex flex-col p-8 rounded-3xl border transition-all duration-300 ${
                plan.highlight 
                  ? 'bg-white border-[#003466] shadow-2xl shadow-blue-900/10 scale-105 z-10' 
                  : 'bg-white border-slate-200 shadow-sm hover:shadow-md'
              }`}
            >
              {plan.highlight && (
                <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-[#003466] text-white text-[10px] font-black uppercase tracking-widest py-1 px-4 rounded-full">
                  Phổ biến nhất
                </div>
              )}

              <div className="mb-8">
                <h3 className="text-xl font-bold text-slate-800 mb-2">{plan.name}</h3>
                <div className="flex items-baseline gap-1">
                  <span className="text-4xl font-black text-[#003466]">{plan.price}</span>
                  {plan.price !== "Liên hệ" && <span className="text-slate-400 font-semibold">/tháng</span>}
                </div>
                <p className="text-sm text-slate-500 mt-2">{plan.description}</p>
              </div>

              <ul className="flex-1 space-y-4 mb-8">
                {plan.features.map((feature, fIdx) => (
                  <li key={fIdx} className="flex items-start gap-3 text-sm text-slate-600">
                    <span className="material-symbols-outlined text-green-500 text-[20px]">check_circle</span>
                    {feature}
                  </li>
                ))}
              </ul>

              <button className={`w-full py-4 rounded-xl font-bold transition-all active:scale-95 ${
                plan.highlight 
                  ? 'bg-[#003466] text-white shadow-lg shadow-blue-900/20 hover:bg-[#002850]' 
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}>
                {plan.buttonText}
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default PricingPage;