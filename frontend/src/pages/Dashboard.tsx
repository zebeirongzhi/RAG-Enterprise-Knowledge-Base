import { useEffect, useState } from "react";
import { Row, Col, Card, Statistic, Typography } from "antd";
import { FolderOutlined, FileOutlined, MessageOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import client from "../api/client";

export default function Dashboard() {
  const [stats, setStats] = useState({ products: 0, documents: 0, conversations: 0 });
  const navigate = useNavigate();

  useEffect(() => {
    Promise.all([
      client.get("/api/products"),
      client.get("/api/documents/count"),
      client.get("/api/chat/conversations?today=true"),
    ]).then(([productsRes, docsRes, convsRes]) => {
      setStats({
        products: productsRes.data.length,
        documents: docsRes.data.count,
        conversations: convsRes.data.length,
      });
    }).catch(() => {});
  }, []);

  return (
    <div>
      <Typography.Title level={4}>知识库概览</Typography.Title>
      <Row gutter={24} style={{ marginTop: 24 }}>
        <Col xs={24} sm={8}>
          <Card hoverable onClick={() => navigate("/knowledge")}>
            <Statistic title="产品线" value={stats.products} prefix={<FolderOutlined />} />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card hoverable onClick={() => navigate("/knowledge")}>
            <Statistic title="文档总数" value={stats.documents} prefix={<FileOutlined />} />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card hoverable onClick={() => navigate("/chat")}>
            <Statistic title="今日问答" value={stats.conversations} prefix={<MessageOutlined />} />
          </Card>
        </Col>
      </Row>
    </div>
  );
}
