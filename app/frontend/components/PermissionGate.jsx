import React from 'react';
import { useStore } from '../state/store';

/**
 * PermissionGate Component
 * Hides children if the user doesn't have the required permission or role.
 */
const PermissionGate = ({ children, requires, type = 'permission' }) => {
  const { role, permissions } = useStore();

  // Admin luôn có quyền truy cập mọi thứ
  if (role === 'admin' || permissions.includes('system:all')) return <>{children}</>;

  if (type === 'role') {
    return role === requires ? <>{children}</> : null;
  }

  // Kiểm tra permission cụ thể
  const hasPermission = permissions.includes(requires);
  
  return hasPermission ? <>{children}</> : null;
};

export default PermissionGate;