## Orders ETL Frontend

Frontend React (Vite + TypeScript) dùng để thao tác với API ETL ở backend (`etl_be`).

### Cài đặt

```bash
cd etl_fe
npm install
```

### Chạy development

Đảm bảo backend đã chạy (ví dụ bằng Docker Compose, API ở `http://localhost:8000`), sau đó:

```bash
npm run dev
```

App sẽ mở tại `http://localhost:5173`.

### Tính năng

- Upload CSV cho 2 nguồn:
  - `Đơn hàng Online` → gọi `POST /upload/online`
  - `Đơn hàng Offline` → gọi `POST /upload/offline`
- Dashboard:
  - Bảng **orders_clean** → gọi `GET /orders/clean`
  - Bảng **orders_error** → gọi `GET /orders/error`
- Kiểm tra nhanh trạng thái API qua `/health`.


