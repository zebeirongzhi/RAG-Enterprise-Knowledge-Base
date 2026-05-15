import { useEffect, useState } from "react";
import { Table, Select, Button, Modal, Form, Input, Popconfirm, message, Typography, Space } from "antd";
import { PlusOutlined, DeleteOutlined } from "@ant-design/icons";
import client from "../api/client";
import type { UserInfo } from "../types";

export default function UserManagement() {
  const [users, setUsers] = useState<UserInfo[]>([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [form] = Form.useForm();

  const loadUsers = () => client.get("/api/users").then(r => setUsers(r.data));

  useEffect(() => { loadUsers(); }, []);

  const changeRole = async (userId: number, newRole: string) => {
    await client.put(`/api/users/${userId}`, { role: newRole });
    message.success("角色已更新");
    loadUsers();
  };

  const deleteUser = async (userId: number) => {
    await client.delete(`/api/users/${userId}`);
    message.success("已删除");
    loadUsers();
  };

  const createUser = async (values: { username: string; password: string; role: string }) => {
    await client.post("/api/users", values);
    message.success("用户创建成功");
    setModalOpen(false);
    form.resetFields();
    loadUsers();
  };

  const columns = [
    { title: "ID", dataIndex: "id", key: "id", width: 80 },
    { title: "用户名", dataIndex: "username", key: "username" },
    {
      title: "角色", dataIndex: "role", key: "role",
      render: (role: string, record: UserInfo) => (
        <Select value={role} style={{ width: 120 }} onChange={v => changeRole(record.id, v)}>
          <Select.Option value="admin">管理员</Select.Option>
          <Select.Option value="customer">客户</Select.Option>
        </Select>
      )
    },
    { title: "创建时间", dataIndex: "created_at", key: "created_at", render: (v: string) => new Date(v).toLocaleDateString("zh-CN") },
    {
      title: "操作", key: "action", width: 80,
      render: (_: unknown, record: UserInfo) => (
        <Popconfirm title="确定删除此用户？" onConfirm={() => deleteUser(record.id)}>
          <Button size="small" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      )
    },
  ];

  return (
    <div>
      <Space style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <Typography.Title level={4} style={{ margin: 0 }}>用户管理</Typography.Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>新增用户</Button>
      </Space>
      <Table rowKey="id" dataSource={users} columns={columns} />

      <Modal title="新增用户" open={modalOpen} onCancel={() => { setModalOpen(false); form.resetFields(); }} footer={null}>
        <Form form={form} onFinish={createUser} layout="vertical">
          <Form.Item name="username" rules={[
            { required: true, message: "请输入用户名" },
            { min: 3, max: 50, message: "3-50个字符" },
            { pattern: /^[a-zA-Z0-9_]+$/, message: "仅支持字母、数字、下划线" },
          ]}>
            <Input placeholder="用户名" />
          </Form.Item>
          <Form.Item name="password" rules={[
            { required: true, message: "请输入密码" },
            { min: 6, max: 128, message: "6-128个字符" },
          ]}>
            <Input.Password placeholder="密码" />
          </Form.Item>
          <Form.Item name="role" initialValue="customer">
            <Select>
              <Select.Option value="customer">客户</Select.Option>
              <Select.Option value="admin">管理员</Select.Option>
            </Select>
          </Form.Item>
          <Button type="primary" htmlType="submit" block>创建</Button>
        </Form>
      </Modal>
    </div>
  );
}
