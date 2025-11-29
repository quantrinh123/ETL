import React, { useEffect, useState } from "react";
import {
  checkHealth,
  getOrdersClean,
  getOrdersError,
  OrderItem,
} from "./api";
import UploadCard from "./components/UploadCard";
import OrdersTable from "./components/OrdersTable";

type TabKey = "upload" | "dashboard";

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabKey>("upload");
  const [apiHealthy, setApiHealthy] = useState<boolean | null>(null);

  const [cleanOrders, setCleanOrders] = useState<OrderItem[]>([]);
  const [errorOrders, setErrorOrders] = useState<OrderItem[]>([]);
  const [loadingClean, setLoadingClean] = useState(false);
  const [loadingError, setLoadingError] = useState(false);
  const [errorClean, setErrorClean] = useState<string | null>(null);
  const [errorError, setErrorError] = useState<string | null>(null);

  useEffect(() => {
    checkHealth().then(setApiHealthy);
  }, []);

  const loadClean = async () => {
    setLoadingClean(true);
    setErrorClean(null);
    try {
      const res = await getOrdersClean(100);
      setCleanOrders(res.items);
    } catch {
      setErrorClean("Không thể tải dữ liệu sạch từ API.");
    } finally {
      setLoadingClean(false);
    }
  };

  const loadError = async () => {
    setLoadingError(true);
    setErrorError(null);
    try {
      const res = await getOrdersError(100);
      setErrorOrders(res.items);
    } catch {
      setErrorError("Không thể tải dữ liệu lỗi từ API.");
    } finally {
      setLoadingError(false);
    }
  };

  useEffect(() => {
    if (activeTab === "dashboard") {
      void loadClean();
      void loadError();
    }
  }, [activeTab]);

  return (
    <div className="app">
      <header className="app-header">
        <div>
          <h1>Orders ETL Console</h1>
          <p className="subtitle">
            Quản lý pipeline tích hợp đơn hàng online & offline.
          </p>
        </div>
        <div className="status-indicator">
          <span
            className={`dot ${
              apiHealthy === null ? "pending" : apiHealthy ? "ok" : "down"
            }`}
          />
          <span className="status-text">
            {apiHealthy === null
              ? "Đang kiểm tra API..."
              : apiHealthy
              ? "API online"
              : "API offline"}
          </span>
        </div>
      </header>

      <nav className="tabs">
        <button
          className={`tab ${activeTab === "upload" ? "active" : ""}`}
          onClick={() => setActiveTab("upload")}
        >
          Upload CSV
        </button>
        <button
          className={`tab ${activeTab === "dashboard" ? "active" : ""}`}
          onClick={() => setActiveTab("dashboard")}
        >
          Data Dashboard
        </button>
      </nav>

      <main className="app-main">
        {activeTab === "upload" && (
          <section className="grid-2">
            <UploadCard
              source="online"
              title="Đơn hàng Online"
              description="Upload file CSV đơn hàng từ kênh online (website, app...)."
            />
            <UploadCard
              source="offline"
              title="Đơn hàng Offline"
              description="Upload file CSV đơn hàng từ cửa hàng, POS hoặc nguồn nội bộ."
            />
          </section>
        )}

        {activeTab === "dashboard" && (
          <section className="grid-1-1">
            <OrdersTable
              title="Dữ liệu sạch (orders_clean)"
              items={cleanOrders}
              loading={loadingClean}
              error={errorClean}
              onReload={loadClean}
            />
            <OrdersTable
              title="Dữ liệu lỗi (orders_error)"
              items={errorOrders}
              loading={loadingError}
              error={errorError}
              onReload={loadError}
              isErrorTable
            />
          </section>
        )}
      </main>

      <footer className="app-footer">
        <span>© {new Date().getFullYear()} Orders ETL Demo</span>
      </footer>
    </div>
  );
};

export default App;


