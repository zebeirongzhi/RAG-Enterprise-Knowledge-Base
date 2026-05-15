import { Outlet, useNavigate, useLocation } from "react-router-dom";
import { Layout, Menu, Button, Typography } from "antd";
import {
  DashboardOutlined, FolderOutlined, MessageOutlined,
  UserOutlined, LogoutOutlined
} from "@ant-design/icons";
import { useAuthStore } from "../stores/authStore";

const { Header, Sider, Content } = Layout;

export default function AppLayout() {
  const { role, username, logout } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    { key: "/", icon: <DashboardOutlined />, label: "首页" },
    ...(role === "admin" ? [{ key: "/knowledge", icon: <FolderOutlined />, label: "知识库" }] : []),
    { key: "/chat", icon: <MessageOutlined />, label: "问答" },
    ...(role === "admin" ? [{ key: "/users", icon: <UserOutlined />, label: "用户管理" }] : []),
  ];

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sider breakpoint="lg" collapsedWidth="0">
        <div style={{ height: 64, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <Typography.Text strong style={{ color: "#fff", fontSize: 18 }}>企业知识库</Typography.Text>
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header style={{ background: "#fff", padding: "0 24px", display: "flex", justifyContent: "flex-end", alignItems: "center", gap: 16 }}>
          <span>{username}（{role === "admin" ? "管理员" : "客户"}）</span>
          <Button icon={<LogoutOutlined />} onClick={() => { logout(); navigate("/login"); }}>退出</Button>
        </Header>
        <Content style={{ margin: 24, background: "#fff", padding: 24, borderRadius: 8 }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
