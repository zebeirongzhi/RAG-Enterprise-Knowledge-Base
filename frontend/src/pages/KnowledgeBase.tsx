import { useEffect, useState } from "react";
import { Row, Col, Card, List, Button, Modal, Form, Input, Upload, Tag, Popconfirm, message, Typography } from "antd";
import { PlusOutlined, DeleteOutlined, UploadOutlined } from "@ant-design/icons";
import client from "../api/client";
import type { Product, ProductModel, Document } from "../types";

export default function KnowledgeBase() {
  const [products, setProducts] = useState<Product[]>([]);
  const [models, setModels] = useState<ProductModel[]>([]);
  const [docs, setDocs] = useState<Document[]>([]);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [selectedModel, setSelectedModel] = useState<ProductModel | null>(null);
  const [productModalOpen, setProductModalOpen] = useState(false);
  const [modelModalOpen, setModelModalOpen] = useState(false);

  const loadProducts = () => client.get("/api/products").then(r => setProducts(r.data));
  const loadModels = (productId: number) => client.get(`/api/products/${productId}/models`).then(r => setModels(r.data));
  const loadDocs = (modelId: number) => client.get(`/api/models/${modelId}/docs`).then(r => setDocs(r.data));

  useEffect(() => { loadProducts(); }, []);

  const handleProductClick = (p: Product) => {
    setSelectedProduct(p);
    setSelectedModel(null);
    setDocs([]);
    loadModels(p.id);
  };

  const handleModelClick = (m: ProductModel) => {
    setSelectedModel(m);
    loadDocs(m.id);
  };

  // Auto-refresh document list while any doc is processing
  useEffect(() => {
    if (!selectedModel) return;
    const hasProcessing = docs.some(d => d.status === "processing");
    if (!hasProcessing) return;
    const timer = setInterval(() => loadDocs(selectedModel.id), 3000);
    return () => clearInterval(timer);
  }, [docs, selectedModel]);

  const handleUpload = async (modelId: number, options: any) => {
    const formData = new FormData();
    formData.append("file", options.file);
    formData.append("model_id", String(modelId));
    try {
      await client.post("/api/documents/upload", formData);
      message.success("上传成功");
      loadDocs(modelId);
    } catch { /* interceptor handles */ }
    options.onSuccess?.();
  };

  const statusColor: Record<string, string> = { processing: "blue", ready: "green", error: "red" };
  const statusText: Record<string, string> = { processing: "处理中", ready: "就绪", error: "失败" };

  return (
    <div>
      <Typography.Title level={4}>知识库管理</Typography.Title>
      <Row gutter={16}>
        {/* Products */}
        <Col span={8}>
          <Card title="产品线" extra={<Button icon={<PlusOutlined />} size="small" onClick={() => setProductModalOpen(true)}>新增</Button>}>
            <List dataSource={products} renderItem={p => (
              <List.Item onClick={() => handleProductClick(p)}
                style={{ cursor: "pointer", background: selectedProduct?.id === p.id ? "#e6f7ff" : undefined, padding: "8px", borderRadius: 4 }}>
                <span>{p.name}</span>
                <Popconfirm title="确定删除？" onConfirm={() => client.delete(`/api/products/${p.id}`).then(loadProducts)}>
                  <Button size="small" danger icon={<DeleteOutlined />} />
                </Popconfirm>
              </List.Item>
            )} />
          </Card>
        </Col>
        {/* Models */}
        <Col span={8}>
          <Card title="型号" extra={selectedProduct && <Button icon={<PlusOutlined />} size="small" onClick={() => setModelModalOpen(true)}>新增</Button>}>
            {selectedProduct ? (
              <List dataSource={models} renderItem={m => (
                <List.Item onClick={() => handleModelClick(m)}
                  style={{ cursor: "pointer", background: selectedModel?.id === m.id ? "#e6f7ff" : undefined, padding: "8px", borderRadius: 4 }}>
                  <span>{m.name}</span>
                  <Popconfirm title="确定删除？" onConfirm={() => client.delete(`/api/models/${m.id}`).then(() => loadModels(selectedProduct!.id))}>
                    <Button size="small" danger icon={<DeleteOutlined />} />
                  </Popconfirm>
                </List.Item>
              )} />
            ) : <Typography.Text type="secondary">请先选择产品</Typography.Text>}
          </Card>
        </Col>
        {/* Documents */}
        <Col span={8}>
          <Card title="文档" extra={selectedModel && (
            <Upload customRequest={(opts: any) => handleUpload(selectedModel!.id, opts)} showUploadList={false} accept=".pdf,.docx,.md,.txt">
              <Button icon={<UploadOutlined />} size="small">上传</Button>
            </Upload>
          )}>
            {selectedModel ? (
              <List dataSource={docs} renderItem={d => (
                <List.Item style={{ padding: 8 }}>
                  <span>{d.filename}</span>
                  <Tag color={statusColor[d.status]}>{statusText[d.status]}</Tag>
                  <Popconfirm title="确定删除？" onConfirm={() => client.delete(`/api/documents/${d.id}`).then(() => loadDocs(selectedModel!.id))}>
                    <Button size="small" danger icon={<DeleteOutlined />} />
                  </Popconfirm>
                </List.Item>
              )} />
            ) : <Typography.Text type="secondary">请先选择型号</Typography.Text>}
          </Card>
        </Col>
      </Row>

      {/* Add Product Modal */}
      <Modal title="新增产品" open={productModalOpen} onCancel={() => setProductModalOpen(false)} footer={null}>
        <Form onFinish={async (v) => { await client.post("/api/products", v); setProductModalOpen(false); loadProducts(); }}>
          <Form.Item name="name" rules={[{ required: true, message: "请输入产品名称" }]}>
            <Input placeholder="产品名称" />
          </Form.Item>
          <Form.Item name="description">
            <Input.TextArea placeholder="描述（选填）" />
          </Form.Item>
          <Button type="primary" htmlType="submit">确定</Button>
        </Form>
      </Modal>

      {/* Add Model Modal */}
      <Modal title="新增型号" open={modelModalOpen} onCancel={() => setModelModalOpen(false)} footer={null}>
        <Form onFinish={async (v) => { await client.post("/api/models", { ...v, product_id: selectedProduct?.id }); setModelModalOpen(false); loadModels(selectedProduct!.id); }}>
          <Form.Item name="name" rules={[{ required: true, message: "请输入型号名称" }]}>
            <Input placeholder="型号名称" />
          </Form.Item>
          <Form.Item name="description">
            <Input.TextArea placeholder="描述（选填）" />
          </Form.Item>
          <Button type="primary" htmlType="submit">确定</Button>
        </Form>
      </Modal>
    </div>
  );
}
