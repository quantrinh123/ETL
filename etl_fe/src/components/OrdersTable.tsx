import React from "react";
import { OrderItem } from "../api";

interface Props {
  title: string;
  items: OrderItem[];
  loading: boolean;
  error: string | null;
  onReload: () => void;
  isErrorTable?: boolean;
}

const OrdersTable: React.FC<Props> = ({
  title,
  items,
  loading,
  error,
  onReload,
  isErrorTable = false,
}) => {
  return (
    <div className="card table-card">
      <div className="table-header">
        <div>
          <h3>{title}</h3>
          <p className="muted">
            Hiển thị {items.length} bản ghi mới nhất (giới hạn 100).
          </p>
        </div>
        <button
          type="button"
          className="btn ghost"
          onClick={onReload}
          disabled={loading}
        >
          {loading ? "Đang tải..." : "Reload"}
        </button>
      </div>
      {error && <p className="status error">{error}</p>}
      <div className="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>Mã đơn</th>
              <th>Nguồn</th>
              <th>Ngày đặt</th>
              <th>Khách hàng</th>
              <th>Số tiền</th>
              <th>Trạng thái</th>
              {isErrorTable && <th>Lý do lỗi</th>}
            </tr>
          </thead>
          <tbody>
            {items.length === 0 && !loading && (
              <tr>
                <td colSpan={isErrorTable ? 7 : 6} className="empty">
                  Chưa có dữ liệu.
                </td>
              </tr>
            )}
            {items.map((item) => (
              <tr key={item.order_id}>
                <td>{item.order_id}</td>
                <td className="badge">{item.source}</td>
                <td>{item.order_date ?? "-"}</td>
                <td>{item.customer_name}</td>
                <td>
                  {typeof item.total_amount === "number"
                    ? item.total_amount.toLocaleString("vi-VN", {
                        style: "currency",
                        currency: "VND",
                      })
                    : item.total_amount}
                </td>
                <td>{item.status}</td>
                {isErrorTable && <td>{item.error_reason}</td>}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default OrdersTable;


