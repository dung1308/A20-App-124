import React, { useEffect, useMemo, useState } from 'react';
import { toast } from 'react-hot-toast';
import api from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';

const ROLE_OPTIONS = ['admin', 'editor', 'user'];
const PERMISSION_OPTIONS = ['system:all', 'db:manage', 'tokens:view', 'profile:edit', 'match:run'];

const DatabaseManagementPage = () => {
  const [status, setStatus] = useState(null);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');
  const [newUser, setNewUser] = useState({
    email: '',
    full_name: '',
    password: '',
    role: 'editor'
  });
  const [permissionDraft, setPermissionDraft] = useState({});

  const filteredUsers = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return users;
    return users.filter((user) =>
      [user.email, user.user_id, user.full_name, user.role]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(q))
    );
  }, [search, users]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [dbStatus, userData] = await Promise.all([
        api.getDbStatus(),
        api.getAdminUsers()
      ]);
      setStatus(dbStatus);
      setUsers(userData.users || []);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Không thể truy cập thông tin hệ thống.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateUser = async (roleOverride) => {
    if (!newUser.email || !newUser.password) {
      toast.error('Email và mật khẩu là bắt buộc.');
      return;
    }

    setSaving(true);
    try {
      await api.createAdminUser({ ...newUser, role: roleOverride || newUser.role });
      toast.success(`Đã thêm ${roleOverride || newUser.role}.`);
      setNewUser({ email: '', full_name: '', password: '', role: 'editor' });
      loadData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Không thể tạo user.');
    } finally {
      setSaving(false);
    }
  };

  const handleRoleChange = async (userId, role) => {
    try {
      await api.updateAdminUserRole(userId, role);
      toast.success(`Đã đổi role thành ${role}.`);
      loadData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Không thể đổi role.');
    }
  };

  const handlePermission = async (userId, action, permission) => {
    if (!permission) {
      toast.error('Chọn permission trước.');
      return;
    }

    try {
      if (action === 'grant') {
        await api.grantAdminUserPermission(userId, permission);
        toast.success(`Đã grant ${permission}.`);
      } else {
        await api.revokeAdminUserPermission(userId, permission);
        toast.success(`Đã revoke ${permission}.`);
      }
      loadData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Không thể cập nhật permission.');
    }
  };

  const handleBlacklist = async (userId, blacklisted) => {
    try {
      await api.updateAdminUserBlacklist(userId, blacklisted);
      toast.success(blacklisted ? 'Đã blacklist user.' : 'Đã gỡ blacklist user.');
      loadData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Không thể cập nhật blacklist.');
    }
  };

  if (loading) return <LoadingSpinner fullPage />;

  return (
    <div className="p-8 h-full overflow-y-auto">
      <div className="max-w-7xl mx-auto space-y-8">
        <header className="border-b-4 border-primary pb-4">
          <h1 className="text-3xl font-black text-primary tracking-tight">System / PostgreSQL Database</h1>
          <p className="text-slate-500 font-medium mt-1">Kiểm tra kết nối database và quản trị tài khoản hệ thống.</p>
        </header>

        {error && (
          <div className="bg-red-50 text-red-700 p-4 rounded-xl border border-red-100">
            {error}
          </div>
        )}

        {status && (
          <section className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <StatusCard label="Trạng thái" value={status.status === 'connected' ? 'Đã kết nối' : 'Mất kết nối'} tone={status.status === 'connected' ? 'green' : 'red'} />
            <StatusCard label="Database" value={`${status.database} (${status.type})`} />
            <StatusCard label="Users" value={status.user_counts?.total || 0} />
            <StatusCard label="Blacklisted" value={status.user_counts?.blacklisted || 0} tone="red" />
          </section>
        )}

        <section className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
          <div className="p-6 border-b border-slate-100">
            <h2 className="text-sm font-black text-slate-800 uppercase tracking-wider">Thêm Admin / Editor</h2>
            <p className="text-xs text-slate-500 mt-1">Tạo user trực tiếp trong PostgreSQL. Role có thể đổi lại trong bảng bên dưới.</p>
          </div>
          <div className="p-6 grid grid-cols-1 md:grid-cols-5 gap-4">
            <input className={inputClass} placeholder="Email" value={newUser.email} onChange={(e) => setNewUser({ ...newUser, email: e.target.value })} />
            <input className={inputClass} placeholder="Tên hiển thị" value={newUser.full_name} onChange={(e) => setNewUser({ ...newUser, full_name: e.target.value })} />
            <input className={inputClass} placeholder="Mật khẩu tạm thời" type="password" value={newUser.password} onChange={(e) => setNewUser({ ...newUser, password: e.target.value })} />
            <select className={inputClass} value={newUser.role} onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}>
              {ROLE_OPTIONS.map((role) => <option key={role} value={role}>{role}</option>)}
            </select>
            <div className="flex gap-2">
              <button disabled={saving} onClick={() => handleCreateUser('admin')} className="flex-1 px-4 py-3 bg-primary text-white rounded-xl text-xs font-black uppercase tracking-widest disabled:opacity-50">Add admin</button>
              <button disabled={saving} onClick={() => handleCreateUser('editor')} className="flex-1 px-4 py-3 bg-slate-900 text-white rounded-xl text-xs font-black uppercase tracking-widest disabled:opacity-50">Add editor</button>
            </div>
          </div>
        </section>

        <section className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
          <div className="p-6 border-b border-slate-100 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <h2 className="text-sm font-black text-slate-800 uppercase tracking-wider">Users trong PostgreSQL</h2>
              <p className="text-xs text-slate-500 mt-1">Grant/revoke permission, đổi role, hoặc blacklist user.</p>
            </div>
            <div className="flex gap-2">
              <input className={`${inputClass} w-72`} placeholder="Tìm email, tên, role..." value={search} onChange={(e) => setSearch(e.target.value)} />
              <button onClick={loadData} className="px-4 py-2 bg-white border border-slate-200 rounded-xl text-xs font-black uppercase tracking-widest text-primary hover:bg-slate-50">Refresh</button>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-slate-500 font-bold uppercase text-[10px] tracking-widest">
                <tr>
                  <th className="px-6 py-4">User</th>
                  <th className="px-6 py-4">Role</th>
                  <th className="px-6 py-4">Permissions</th>
                  <th className="px-6 py-4">Grant / Revoke</th>
                  <th className="px-6 py-4 text-right">Blacklist</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredUsers.map((user) => {
                  const userId = user.email || user.user_id;
                  const selectedPermission = permissionDraft[userId] || PERMISSION_OPTIONS[0];

                  return (
                    <tr key={userId} className={user.blacklisted ? 'bg-red-50/40' : ''}>
                      <td className="px-6 py-4">
                        <p className="font-bold text-slate-800">{user.email || user.user_id}</p>
                        <p className="text-xs text-slate-400">{user.full_name || 'No display name'}</p>
                      </td>
                      <td className="px-6 py-4">
                        <select className={`${inputClass} min-w-28`} value={user.role || 'user'} onChange={(e) => handleRoleChange(userId, e.target.value)}>
                          {ROLE_OPTIONS.map((role) => <option key={role} value={role}>{role}</option>)}
                        </select>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex flex-wrap gap-1 max-w-xs">
                          {(user.permissions || []).length > 0 ? (
                            user.permissions.map((permission) => (
                              <span key={permission} className="px-2 py-1 bg-blue-50 text-blue-700 border border-blue-100 rounded text-[10px] font-bold">{permission}</span>
                            ))
                          ) : (
                            <span className="text-xs text-slate-400 italic">No custom permissions</span>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex gap-2 min-w-[320px]">
                          <select className={inputClass} value={selectedPermission} onChange={(e) => setPermissionDraft({ ...permissionDraft, [userId]: e.target.value })}>
                            {PERMISSION_OPTIONS.map((permission) => <option key={permission} value={permission}>{permission}</option>)}
                          </select>
                          <button onClick={() => handlePermission(userId, 'grant', selectedPermission)} className="px-3 py-2 bg-emerald-600 text-white rounded-lg text-[10px] font-black uppercase">Grant</button>
                          <button onClick={() => handlePermission(userId, 'revoke', selectedPermission)} className="px-3 py-2 bg-white border border-slate-200 text-slate-600 rounded-lg text-[10px] font-black uppercase">Revoke</button>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <button
                          onClick={() => handleBlacklist(userId, !user.blacklisted)}
                          className={`px-4 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest ${
                            user.blacklisted
                              ? 'bg-white text-red-600 border border-red-200'
                              : 'bg-red-600 text-white border border-red-600'
                          }`}
                        >
                          {user.blacklisted ? 'Unblacklist' : 'Blacklist'}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>
  );
};

const inputClass = 'px-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium text-slate-700 outline-none focus:ring-2 focus:ring-primary/20';

const StatusCard = ({ label, value, tone = 'slate' }) => {
  const toneClass = tone === 'green' ? 'text-emerald-600' : tone === 'red' ? 'text-red-600' : 'text-slate-800';
  return (
    <div className="p-4 bg-white border border-slate-200 rounded-2xl shadow-sm">
      <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{label}</p>
      <p className={`text-lg font-black mt-1 ${toneClass}`}>{value}</p>
    </div>
  );
};

export default DatabaseManagementPage;
