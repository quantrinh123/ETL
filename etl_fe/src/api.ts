import axios from "axios";

const api = axios.create({
  baseURL: "/api",
});

export interface UploadResponse {
  published: number;
}

export interface OrderItem {
  order_id: string;
  source: string;
  order_date: string | null;
  customer_id: string | null;
  customer_name: string;
  total_amount: number;
  status: string;
  created_at: string | null;
  error_reason?: string;
}

export interface OrdersResponse {
  items: OrderItem[];
  count: number;
}

export async function uploadCsv(
  source: "online" | "offline",
  file: File
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await api.post<UploadResponse>(`/upload/${source}`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function getOrdersClean(limit = 100): Promise<OrdersResponse> {
  const { data } = await api.get<OrdersResponse>("/orders/clean", {
    params: { limit },
  });
  return data;
}

export async function getOrdersError(limit = 100): Promise<OrdersResponse> {
  const { data } = await api.get<OrdersResponse>("/orders/error", {
    params: { limit },
  });
  return data;
}

export async function checkHealth(): Promise<boolean> {
  try {
    const { data } = await api.get<{ status: string }>("/health");
    return data.status === "ok";
  } catch {
    return false;
  }
}


