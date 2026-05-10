import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { 
  PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer, 
  BarChart, Bar, XAxis, YAxis, CartesianGrid 
} from 'recharts';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

const AdminDashboard = () => {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [timeWindow, setTimeWindow] = useState(336); // Default 2 weeks

  useEffect(() => {
    fetchMetrics();
  }, [timeWindow]);

  const fetchMetrics = async () => {
    try {
      setLoading(true);
      const data = await api.getMetrics(timeWindow);
      setMetrics(data);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch metrics:', err);
      setError('Không thể tải dữ liệu thống kê. Vui lòng kiểm tra quyền quản trị.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="p-8 text-center">Đang tải dữ liệu hệ thống...</div>;
  if (error) return <div className="p-8 text-red-500 text-center">{error}</div>;
  if (!metrics) return null;

  // Transform route distribution for Recharts
  const routeData = Object.entries(metrics.route_distribution || {}).map(([name, value]) => ({
    name: name.toUpperCase(),
    value
  }));

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-2xl font-bold text-gray-800">Bảng điều khiển Quản trị (PMF Metrics)</h1>
        
        <select 
          className="bg-white border border-gray-300 rounded-md px-4 py-2"
          value={timeWindow}
          onChange={(e) => setTimeWindow(Number(e.target.value))}
        >
          <option value={24}>24 Giờ qua</option>
          <option value={168}>7 Ngày qua</option>
          <option value={336}>14 Ngày qua</option>
          <option value={720}>30 Ngày qua</option>
        </select>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <MetricCard 
          title="Tổng số yêu cầu" 
          value={metrics.total_requests} 
          sub="Lượt tương tác"
        />
        <MetricCard 
          title="Tỷ lệ AI Giải quyết" 
          value={`${(metrics.ai_resolution_rate * 100).toFixed(1)}%`} 
          color="text-green-600"
        />
        <MetricCard 
          title="Thời gian phản hồi TB" 
          value={`${metrics.avg_response_time_ms}ms`} 
          sub="Độ trễ hệ thống"
        />
        <MetricCard 
          title="Tỷ lệ Chuyển chuyên viên" 
          value={`${(metrics.human_fallback_rate * 100).toFixed(1)}%`} 
          color="text-orange-500"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Route Distribution Chart */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold mb-4">Phân bổ Luồng xử lý (Intent Routing)</h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={routeData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={5}
                  dataKey="value"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                >
                  {routeData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Performance Overview */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold mb-4">Hiệu suất Giải quyết (Resolution)</h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={[
                  { name: 'AI Resolved', value: metrics.ai_resolution_rate * 100 },
                  { name: 'Human Fallback', value: metrics.human_fallback_rate * 100 }
                ]}
                margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis unit="%" />
                <Tooltip formatter={(value) => `${value.toFixed(1)}%`} />
                <Bar dataKey="value" fill="#8884d8" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <p className="mt-4 text-sm text-gray-500 italic">
            * Dữ liệu được tính toán dựa trên bảng AuditLog của hệ thống.
          </p>
        </div>
      </div>
      
      <div className="mt-8 text-right text-xs text-gray-400">
        Cập nhật lần cuối: {new Date(metrics.generated_at).toLocaleString('vi-VN')}
      </div>
    </div>
  );
};

const MetricCard = ({ title, value, sub, color = "text-blue-600" }) => (
  <div className="bg-white p-5 rounded-lg shadow-sm border border-gray-200">
    <p className="text-sm font-medium text-gray-500 uppercase tracking-wider">{title}</p>
    <div className="flex items-baseline mt-2">
      <h2 className={`text-3xl font-bold ${color}`}>{value}</h2>
      {sub && <span className="ml-2 text-sm text-gray-400">{sub}</span>}
    </div>
  </div>
);

export default AdminDashboard;