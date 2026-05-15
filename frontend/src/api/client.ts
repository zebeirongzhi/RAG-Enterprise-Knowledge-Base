import axios from "axios";
import { message } from "antd";

const client = axios.create({
  baseURL: "http://localhost:8000",
  timeout: 60000,
});

client.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

client.interceptors.response.use(
  (res) => res,
  (error) => {
    const msg = error.response?.data?.detail || "请求失败";
    message.error(msg);
    if (error.response?.status === 401) {
      localStorage.removeItem("token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export default client;
