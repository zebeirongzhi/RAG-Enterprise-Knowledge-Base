import { useState, useRef, useEffect, useCallback } from "react";
import { Input, Button, Select, Space, Typography, Tag, Spin } from "antd";
import { SendOutlined, RobotOutlined, UserOutlined, PlusOutlined, HistoryOutlined, DeleteOutlined } from "@ant-design/icons";
import ReactMarkdown from "react-markdown";
import type { Components } from "react-markdown";
import client from "../api/client";
import type { Product, ProductModel } from "../types";

function normalizeMarkdown(text: string): string {
  return text
    .replace(/([^\n])\n(#{2,3}\s)/g, "$1\n\n$2")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

const mdStyles: Record<string, React.CSSProperties> = {
  p: { margin: "0 0 1em 0", fontSize: 16, lineHeight: 1.75 },
  strong: { fontSize: 16, fontWeight: 600 },
  li: { fontSize: 16, lineHeight: 1.75, marginBottom: 4 },
  h2: { fontSize: 20, fontWeight: 600, margin: "1.5em 0 0.5em 0", paddingBottom: 8, borderBottom: "1px solid #e8e8e8" },
  h3: { fontSize: 18, fontWeight: 600, margin: "1.2em 0 0.4em 0" },
  blockquote: { margin: "1em 0", padding: "8px 16px", borderLeft: "3px solid #d0d0d0", color: "#555", fontSize: 15, background: "#fafafa", borderRadius: "0 4px 4px 0" },
  ul: { margin: "0.5em 0 1em 0", paddingLeft: 24 },
  ol: { margin: "0.5em 0 1em 0", paddingLeft: 24 },
  code: { background: "#f0f0f0", padding: "2px 6px", borderRadius: 4, fontSize: 14, fontFamily: "Consolas, Monaco, monospace" },
};

const mdComponents: Components = {
  p: ({ children }) => <p style={mdStyles.p}>{children}</p>,
  strong: ({ children }) => <strong style={mdStyles.strong}>{children}</strong>,
  li: ({ children }) => <li style={mdStyles.li}>{children}</li>,
  h2: ({ children }) => <h2 style={mdStyles.h2}>{children}</h2>,
  h3: ({ children }) => <h3 style={mdStyles.h3}>{children}</h3>,
  blockquote: ({ children }) => <blockquote style={mdStyles.blockquote}>{children}</blockquote>,
  ul: ({ children }) => <ul style={mdStyles.ul}>{children}</ul>,
  ol: ({ children }) => <ol style={mdStyles.ol}>{children}</ol>,
  code: ({ children }) => <code style={mdStyles.code}>{children}</code>,
};

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: { filename: string; product_name: string; model_name: string }[];
}

interface ConvItem {
  id: number;
  question: string;
  answer: string;
  sources?: { filename: string; product_name: string; model_name: string }[];
  created_at: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [products, setProducts] = useState<Product[]>([]);
  const [models, setModels] = useState<ProductModel[]>([]);
  const [selectedProduct, setSelectedProduct] = useState<number | undefined>();
  const [selectedModel, setSelectedModel] = useState<number | undefined>();
  const [convs, setConvs] = useState<ConvItem[]>([]);
  const [activeConvId, setActiveConvId] = useState<number | null>(null);
  const chatRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    client.get("/api/products").then(r => setProducts(r.data)).catch(() => {});
  }, []);

  useEffect(() => {
    if (selectedProduct) {
      client.get(`/api/products/${selectedProduct}/models`).then(r => setModels(r.data)).catch(() => {});
    } else {
      setModels([]);
      setSelectedModel(undefined);
    }
  }, [selectedProduct]);

  const loadConversations = useCallback(() => {
    client.get("/api/chat/conversations").then(r => setConvs(r.data)).catch(() => {});
  }, []);

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  const scrollBottom = () => {
    setTimeout(() => {
      chatRef.current?.scrollTo({ top: chatRef.current.scrollHeight, behavior: "smooth" });
    }, 100);
  };

  const startNewChat = () => {
    setMessages([]);
    setActiveConvId(null);
  };

  const openConversation = (conv: ConvItem) => {
    setActiveConvId(conv.id);
    setMessages([
      { role: "user", content: conv.question },
      { role: "assistant", content: conv.answer, sources: conv.sources },
    ]);
  };

  const deleteConversation = (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    client.delete(`/api/chat/conversations/${id}`).then(() => {
      if (activeConvId === id) {
        setMessages([]);
        setActiveConvId(null);
      }
      loadConversations();
    }).catch(() => {});
  };

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    const question = input.trim();
    setInput("");
    setMessages(prev => [...prev, { role: "user", content: question }]);
    setLoading(true);
    scrollBottom();
    setActiveConvId(null);

    try {
      const token = localStorage.getItem("token");
      const res = await fetch("http://localhost:8000/api/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ question, product_id: selectedProduct, model_id: selectedModel }),
      });

      const reader = res.body?.getReader();
      const decoder = new TextDecoder();
      let answer = "";

      setMessages(prev => [...prev, { role: "assistant", content: "" }]);

      while (reader) {
        const { done, value } = await reader.read();
        if (done) break;
        const text = decoder.decode(value, { stream: true });
        const lines = text.split("\n");
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const raw = line.slice(6);
            if (raw === "[DONE]") break;
            const data = JSON.parse(raw);
            answer += data;
            setMessages(prev => {
              const copy = [...prev];
              copy[copy.length - 1] = { ...copy[copy.length - 1], role: "assistant", content: answer };
              return copy;
            });
            scrollBottom();
          }
        }
      }

      loadConversations();
    } catch {
      setMessages(prev => {
        const copy = [...prev];
        copy[copy.length - 1] = { ...copy[copy.length - 1], content: "AI 服务不可用，请稍后重试" };
        return copy;
      });
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dt: string) => {
    const d = new Date(dt + "Z");
    const now = new Date();
    const stripTime = (t: Date) => new Date(t.getFullYear(), t.getMonth(), t.getDate()).getTime();
    const dayDiff = Math.round((stripTime(now) - stripTime(d)) / 86400000);
    if (dayDiff === 0) return d.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
    if (dayDiff === 1) return "昨天";
    if (dayDiff < 7) return `${dayDiff}天前`;
    return d.toLocaleDateString("zh-CN", { month: "short", day: "numeric" });
  };

  return (
    <div style={{ display: "flex", height: "calc(100vh - 160px)", gap: 0 }}>
      {/* Sidebar */}
      <div style={{
        width: 260, minWidth: 260, borderRight: "1px solid #f0f0f0",
        display: "flex", flexDirection: "column", background: "#fafafa",
      }}>
        <div style={{ padding: "12px 16px" }}>
          <Button type="dashed" icon={<PlusOutlined />} block onClick={startNewChat}>
            新对话
          </Button>
        </div>
        <div style={{ flex: 1, overflow: "auto", padding: "0 8px" }}>
          {convs.length === 0 && (
            <div style={{ textAlign: "center", color: "#bbb", marginTop: 40, fontSize: 13 }}>
              <HistoryOutlined style={{ fontSize: 24, marginBottom: 8 }} />
              <div>暂无历史对话</div>
            </div>
          )}
          {convs.map(c => (
            <div
              key={c.id}
              onClick={() => openConversation(c)}
              style={{
                padding: "10px 12px", marginBottom: 4, borderRadius: 8, cursor: "pointer",
                background: activeConvId === c.id ? "#e6f4ff" : "transparent",
                border: activeConvId === c.id ? "1px solid #91caff" : "1px solid transparent",
                position: "relative",
              }}
              onMouseEnter={e => { if (activeConvId !== c.id) (e.currentTarget as HTMLElement).style.background = "#f0f0f0"; }}
              onMouseLeave={e => { if (activeConvId !== c.id) (e.currentTarget as HTMLElement).style.background = "transparent"; }}
            >
              <div style={{ fontSize: 13, fontWeight: 500, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", marginBottom: 4, paddingRight: 20 }}>
                {c.question}
              </div>
              <Typography.Text type="secondary" style={{ fontSize: 11 }}>
                {formatDate(c.created_at)}
              </Typography.Text>
              <DeleteOutlined
                onClick={e => deleteConversation(c.id, e)}
                style={{ position: "absolute", top: 10, right: 8, fontSize: 12, color: "#bbb", cursor: "pointer" }}
                title="删除对话"
              />
            </div>
          ))}
        </div>
      </div>

      {/* Main chat area */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", paddingLeft: 24 }}>
        <Space style={{ marginBottom: 16 }}>
          <Select placeholder="全部产品" allowClear style={{ width: 180 }}
            options={products.map(p => ({ value: p.id, label: p.name }))}
            value={selectedProduct} onChange={v => setSelectedProduct(v)} />
          <Select placeholder="全部型号" allowClear style={{ width: 180 }}
            options={models.map(m => ({ value: m.id, label: m.name }))}
            value={selectedModel} onChange={v => setSelectedModel(v)} />
        </Space>

        <div ref={chatRef} style={{ flex: 1, overflow: "auto", marginBottom: 16, padding: "16px 0" }}>
          {messages.length === 0 && (
            <div style={{ textAlign: "center", color: "#999", marginTop: 120 }}>
              <RobotOutlined style={{ fontSize: 56, color: "#bbb" }} />
              <p style={{ fontSize: 18, marginTop: 16 }}>我是企业知识库助手，请提出你的问题</p>
            </div>
          )}
          {messages.map((msg, i) => (
            <div key={i} style={{ marginBottom: 24, display: "flex", justifyContent: msg.role === "user" ? "flex-end" : "flex-start", padding: "0 8px" }}>
              <div style={{ display: "flex", maxWidth: "85%", gap: 12 }}>
                {msg.role === "assistant" && (
                  <div style={{ flexShrink: 0, width: 32, height: 32, borderRadius: "50%", background: "#10a37f", display: "flex", alignItems: "center", justifyContent: "center" }}>
                    <RobotOutlined style={{ color: "#fff", fontSize: 16 }} />
                  </div>
                )}
                <div style={{
                  padding: "12px 20px",
                  borderRadius: msg.role === "user" ? "16px 4px 16px 16px" : "4px 16px 16px 16px",
                  background: msg.role === "user" ? "#e8f0fe" : "#fff",
                  border: msg.role === "user" ? "none" : "1px solid #e5e5e5",
                  flex: 1,
                  minWidth: 0,
                }}>
                  {msg.role === "assistant" ? (
                    <div>
                      <ReactMarkdown components={mdComponents}>{normalizeMarkdown(msg.content)}</ReactMarkdown>
                      {loading && i === messages.length - 1 && <Spin size="small" style={{ marginLeft: 8 }} />}
                    </div>
                  ) : (
                    <Typography.Paragraph style={{ margin: 0, whiteSpace: "pre-wrap", fontSize: 16, lineHeight: 1.75 }}>
                      {msg.content}
                    </Typography.Paragraph>
                  )}
                  {msg.sources && msg.sources.length > 0 && (
                    <div style={{ marginTop: 16, paddingTop: 12, borderTop: "1px solid #eee" }}>
                      <Typography.Text type="secondary" style={{ fontSize: 12 }}>参考来源：</Typography.Text>
                      {msg.sources.map((s, j) => (
                        <Tag key={j} color="blue" style={{ fontSize: 12, marginTop: 4 }}>
                          {s.filename}
                        </Tag>
                      ))}
                    </div>
                  )}
                </div>
                {msg.role === "user" && (
                  <div style={{ flexShrink: 0, width: 32, height: 32, borderRadius: "50%", background: "#1677ff", display: "flex", alignItems: "center", justifyContent: "center" }}>
                    <UserOutlined style={{ color: "#fff", fontSize: 16 }} />
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        <div style={{ display: "flex", gap: 8 }}>
          <Input.TextArea value={input} onChange={e => setInput(e.target.value)}
            onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); } }}
            placeholder="输入问题，按 Enter 发送，Shift+Enter 换行..." rows={2} />
          <Button type="primary" icon={<SendOutlined />} onClick={sendMessage} loading={loading}>发送</Button>
        </div>
      </div>
    </div>
  );
}
