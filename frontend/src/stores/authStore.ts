import { create } from "zustand";
import client from "../api/client";

interface AuthState {
  token: string | null;
  role: string;
  username: string;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: localStorage.getItem("token"),
  role: localStorage.getItem("role") || "",
  username: localStorage.getItem("username") || "",
  login: async (username, password) => {
    const res = await client.post("/api/auth/login", { username, password });
    const { access_token, role, username: un } = res.data;
    localStorage.setItem("token", access_token);
    localStorage.setItem("role", role);
    localStorage.setItem("username", un);
    set({ token: access_token, role, username: un });
  },
  logout: () => {
    localStorage.clear();
    set({ token: null, role: "", username: "" });
  },
}));
