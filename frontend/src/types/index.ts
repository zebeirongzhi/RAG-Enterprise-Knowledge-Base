export interface Product {
  id: number;
  name: string;
  description: string;
  created_at: string;
}

export interface ProductModel {
  id: number;
  product_id: number;
  name: string;
  description: string;
  created_at: string;
}

export interface Document {
  id: number;
  model_id: number;
  filename: string;
  file_type: string;
  file_size: number;
  status: "processing" | "ready" | "error";
  chunk_count: number;
  created_at: string;
}

export interface UserInfo {
  id: number;
  username: string;
  role: "admin" | "customer";
  created_at: string;
}
