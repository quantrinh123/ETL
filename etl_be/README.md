## Tích hợp dữ liệu đơn hàng online & offline (RabbitMQ + Docker + FastAPI)

ETL: Upload CSV qua API → RabbitMQ → Consumer validate/transform → ghi thẳng vào Postgres (`orders`, `orders_clean`, `orders_error`) không cần ghi file output/staging.

### Kiến trúc logic

```
CSV (upload/API) → Producer publish → RabbitMQ → Consumer
    → Ghi raw vào PostgreSQL (`orders`) → Validation + Transform → PostgreSQL (`orders_clean`, `orders_error`)
```

- **Upload CSV**: upload qua API (mẫu sẵn: `upload/online_orders.csv`, `upload/offline_orders.csv`).
- **Publish**: chỉ dùng endpoint upload; producer scripts giữ lại để tham khảo, không cần cho luồng chính.
- **Broker**: RabbitMQ chạy Docker (xem `docker-compose.yml`).
- **Consumer**: `app/consumer_orders.py` đọc queue, lưu raw vào `orders`, validate/transform và ghi thẳng vào `orders_clean`/`orders_error`.
- **Database**: PostgreSQL chứa kết quả; không dùng file output/staging.
- Lưu ý: staging/output CSV không còn sinh ra nữa; dữ liệu lưu trực tiếp vào DB.

API FastAPI: `app/main.py` giúp upload/publish CSV và tự tạo bảng qua SQLAlchemy; consumer ghi trực tiếp vào PostgreSQL.

### Cấu trúc thư mục

```
etl_be/
├─ docker-compose.yml
├─ Dockerfile
├─ requirements.txt
├─ README.md
├─ upload/
│  ├─ online_orders.csv
│  └─ offline_orders.csv
├─ app/
│  ├─ __init__.py
│  ├─ config.py
│  ├─ logging_conf.py
│  ├─ utils.py
│  ├─ transform.py
│  ├─ validation.py
│  ├─ main.py
│  ├─ producer_online.py      (demo/tuỳ chọn)
│  ├─ producer_offline.py     (demo/tuỳ chọn)
│  ├─ consumer_orders.py
│  └─ db.py
└─ tests/
   ├─ test_transform.py
   └─ test_validation.py
```

### Chuẩn bị môi trường

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Chạy API + consumer + infra bằng Docker:

```bash
docker compose up --build -d
```

- API: http://localhost:8000 (docs: http://localhost:8000/docs)
- RabbitMQ Management UI: http://localhost:15672 (guest/guest).
- PostgreSQL: localhost:5432 (user: orders_user, pass: orders_pass, db: orders_db).

API khởi động sẽ tự tạo bảng bằng SQLAlchemy (`orders`, `orders_clean`, `orders_error`) nếu `MIGRATE_ON_START=true` (mặc định). Không cần Alembic.

### API chính

- `GET /health` — kiểm tra sống.
- `POST /upload/{source}` — upload CSV và publish (body: multipart với file, UTF-8; `source` = online/offline).
- `GET /orders/clean` — xem dữ liệu sạch (param `limit`, mặc định 100).
- `GET /orders/error` — xem dữ liệu lỗi (param `limit`, mặc định 100).

Ví dụ cURL (dùng file mẫu offline có sẵn):
```bash
curl -X POST -F "file=@./upload/offline_orders.csv" http://localhost:8000/upload/offline
```

### Quy trình demo nhanh

1. `docker compose up --build -d` (khởi động RabbitMQ, Postgres, API, consumer; API tự migrate).
2. Upload CSV (dùng file mẫu):
   ```bash
   curl -X POST -F "file=@./upload/online_orders.csv" http://localhost:8000/upload/online
   curl -X POST -F "file=@./upload/offline_orders.csv" http://localhost:8000/upload/offline
   ```
   (Hoặc upload CSV tuỳ chỉnh bằng `/upload/{source}`)
3. Consumer xử lý queue → lưu raw vào `orders`, kết quả sạch vào `orders_clean`, lỗi vào `orders_error`.
4. Kiểm tra DB:
   ```bash
   docker compose exec postgres psql -U orders_user -d orders_db -c "SELECT * FROM orders;"
   docker compose exec postgres psql -U orders_user -d orders_db -c "SELECT * FROM orders_clean;"
   docker compose exec postgres psql -U orders_user -d orders_db -c "SELECT * FROM orders_error;"
   ```
   Hoặc dùng API đọc nhanh: `GET /orders/clean`, `GET /orders/error`.

### Quy tắc chất lượng dữ liệu

| Trường          | Rule                                                                 |
|-----------------|----------------------------------------------------------------------|
| `order_id`      | không rỗng                                                           |
| `customer_name` | không rỗng, không chứa chữ số, tối đa 50 ký tự                       |
| `total_amount`  | dạng số và > 0                                                       |
| `order_date`    | parse được `YYYY-MM-DD`, `DD/MM/YYYY`, `DD-MM-YYYY`                  |
| `status`        | không rỗng                                                           |

Record hợp lệ → ghi vào `orders_clean`. Record lỗi → `orders_error` với `error_reason`.

### Strategy Pattern trong Validation

Validation được tổ chức dùng **Strategy pattern** (`app/validation.py`):

```
ValidationStrategy (Abstract Base Class)
├─ OrderIdStrategy
├─ CustomerNameStrategy
├─ TotalAmountStrategy
├─ OrderDateStrategy
└─ StatusStrategy

OrderValidator
└─ Sử dụng danh sách strategies để validate record
```

**Lợi ích:**
- Dễ thêm/sửa/xóa rule mới (mỗi rule = 1 strategy)
- Không ảnh hưởng tới các rule khác
- Dễ test từng rule độc lập

**Ví dụ thêm rule mới:**
```python
class PhoneNumberStrategy(ValidationStrategy):
    def validate(self, record: Dict[str, str]) -> List[str]:
        # Implement your validation
        return errors

# Thêm vào OrderValidator.strategies
```

### PostgreSQL Schema

`orders` (raw sau khi upload/publish, giữ giá trị gốc dạng TEXT):
```sql
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR(50) UNIQUE NOT NULL,
    source VARCHAR(20),
    order_date TEXT,
    customer_id TEXT,
    customer_name TEXT,
    total_amount TEXT,
    status TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

`orders_clean` (dữ liệu sạch sau validate/transform):
```sql
CREATE TABLE orders_clean (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR(50) UNIQUE NOT NULL,
    source VARCHAR(20),
    order_date DATE NOT NULL,
    customer_id VARCHAR(50),
    customer_name VARCHAR(100) NOT NULL,
    total_amount NUMERIC(10, 2) NOT NULL,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

`orders_error` (dữ liệu lỗi, giữ nguyên giá trị gốc dạng TEXT + error_reason):
```sql
CREATE TABLE orders_error (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR(50) UNIQUE NOT NULL,
    source VARCHAR(20),
    order_date TEXT,
    customer_id TEXT,
    customer_name TEXT,
    total_amount TEXT,
    status TEXT,
    error_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

Pipeline ghi thẳng vào DB qua SQLAlchemy; không cần file staging/output, không dùng Alembic hay load_from_csv.

### Kiểm thử

```bash
pytest
```

### Mở rộng

- Thêm bảng khách hàng, sản phẩm hoặc enrichment khác trong `transform.py`.
- Thêm các strategy validation mới cho các business rules khác.
- Mở rộng schema PostgreSQL với indexes, foreign keys, v.v.
- Nếu cần demo script producer, có thể đóng gói chúng vào container riêng.

