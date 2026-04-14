"use client";

import { useCallback, useEffect, useState } from "react";
import {
  fetchUsers,
  updateUser,
  deactivateUser,
  reactivateUser,
} from "@/lib/api-client";
import type { UserListItem } from "@/lib/types";

const ROLE_STYLES: Record<string, string> = {
  admin: "bg-purple-100 text-purple-800",
  editor: "bg-blue-100 text-blue-800",
  viewer: "bg-gray-100 text-gray-700",
};

const ROLE_OPTIONS = [
  { value: "admin", label: "Admin" },
  { value: "editor", label: "Editor" },
  { value: "viewer", label: "Viewer" },
];

export default function UsersPage() {
  const [users, setUsers] = useState<UserListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editRole, setEditRole] = useState("");

  const loadUsers = useCallback(async () => {
    try {
      setLoading(true);
      const data = await fetchUsers();
      setUsers(data);
    } catch {
      setError("Không thể tải danh sách người dùng");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadUsers();
  }, [loadUsers]);

  async function handleRoleChange(userId: string) {
    try {
      await updateUser(userId, { role: editRole });
      setEditingId(null);
      await loadUsers();
    } catch {
      setError("Không thể cập nhật vai trò");
    }
  }

  async function handleToggleActive(user: UserListItem) {
    try {
      if (user.is_active) {
        await deactivateUser(user.id);
      } else {
        await reactivateUser(user.id);
      }
      await loadUsers();
    } catch {
      setError("Không thể thay đổi trạng thái");
    }
  }

  return (
    <div className="h-full overflow-y-auto">
      <div className="p-4 md:p-6 max-w-4xl mx-auto">
        <h1 className="text-lg font-bold text-gray-900">Quản lý người dùng</h1>
        <p className="text-sm text-gray-500 mt-1">
          Quản lý tài khoản và phân quyền trong tổ chức
        </p>

        {error && (
          <div className="mt-3 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700">
            {error}
            <button
              onClick={() => setError(null)}
              className="ml-2 text-red-500 hover:text-red-700"
            >
              x
            </button>
          </div>
        )}

        {loading ? (
          <p className="text-sm text-gray-500 mt-4">Đang tải...</p>
        ) : (
          <div className="mt-4 bg-white border border-gray-200 rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="text-left px-4 py-2 font-medium text-gray-600">
                    Tên
                  </th>
                  <th className="text-left px-4 py-2 font-medium text-gray-600 hidden md:table-cell">
                    Email
                  </th>
                  <th className="text-left px-4 py-2 font-medium text-gray-600">
                    Vai trò
                  </th>
                  <th className="text-left px-4 py-2 font-medium text-gray-600">
                    Trạng thái
                  </th>
                  <th className="text-right px-4 py-2 font-medium text-gray-600">
                    Hành động
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {users.map((user) => (
                  <tr key={user.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <p className="font-medium text-gray-900">{user.full_name}</p>
                      <p className="text-xs text-gray-500 md:hidden">{user.email}</p>
                    </td>
                    <td className="px-4 py-3 text-gray-600 hidden md:table-cell">
                      {user.email}
                    </td>
                    <td className="px-4 py-3">
                      {editingId === user.id ? (
                        <div className="flex items-center gap-1">
                          <select
                            value={editRole}
                            onChange={(e) => setEditRole(e.target.value)}
                            className="text-xs border border-gray-300 rounded px-1.5 py-1"
                          >
                            {ROLE_OPTIONS.map((opt) => (
                              <option key={opt.value} value={opt.value}>
                                {opt.label}
                              </option>
                            ))}
                          </select>
                          <button
                            onClick={() => handleRoleChange(user.id)}
                            className="text-xs text-brand-600 hover:text-brand-700 font-medium"
                          >
                            Lưu
                          </button>
                          <button
                            onClick={() => setEditingId(null)}
                            className="text-xs text-gray-400 hover:text-gray-600"
                          >
                            Hủy
                          </button>
                        </div>
                      ) : (
                        <span
                          className={`px-2 py-0.5 rounded text-xs font-medium ${
                            ROLE_STYLES[user.role] || ROLE_STYLES.viewer
                          }`}
                        >
                          {user.role}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-2 py-0.5 rounded text-xs font-medium ${
                          user.is_active
                            ? "bg-green-100 text-green-800"
                            : "bg-red-100 text-red-800"
                        }`}
                      >
                        {user.is_active ? "Hoạt động" : "Đã vô hiệu"}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-2">
                        {editingId !== user.id && (
                          <button
                            onClick={() => {
                              setEditingId(user.id);
                              setEditRole(user.role);
                            }}
                            className="text-xs text-brand-600 hover:text-brand-700"
                          >
                            Sửa
                          </button>
                        )}
                        <button
                          onClick={() => handleToggleActive(user)}
                          className={`text-xs ${
                            user.is_active
                              ? "text-red-600 hover:text-red-700"
                              : "text-green-600 hover:text-green-700"
                          }`}
                        >
                          {user.is_active ? "Vô hiệu hóa" : "Kích hoạt"}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {users.length === 0 && (
              <p className="text-sm text-gray-500 text-center py-6">
                Chưa có người dùng nào
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
