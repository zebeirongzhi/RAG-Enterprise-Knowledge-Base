import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { ConfigProvider } from "antd";
import zhCN from "antd/locale/zh_CN";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import KnowledgeBase from "./pages/KnowledgeBase";
import ChatPage from "./pages/Chat";
import UserManagement from "./pages/UserManagement";
import AppLayout from "./components/AppLayout";

function Protected() {
  const token = localStorage.getItem("token");
  if (!token) return <Navigate to="/login" replace />;
  return <AppLayout />;
}

export default function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/*" element={<Protected />}>
            <Route index element={<Dashboard />} />
            <Route path="knowledge" element={<KnowledgeBase />} />
            <Route path="chat" element={<ChatPage />} />
            <Route path="users" element={<UserManagement />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  );
}
