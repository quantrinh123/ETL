## Tích hợp dữ liệu đơn hàng online & offline (RabbitMQ + Docker)

Đồ án demo này minh hoạ quy trình ETL chuẩn cho đề tài "Tích hợp dữ liệu đơn hàng online & offline sử dụng RabbitMQ và Docker".

### Kiến trúc logic

```
CSV sources → Producers (online/offline) → RabbitMQ queue → Consumer
    → Staging (raw CSV) → Validation + Transform → Clean/Error outputs
    → PostgreSQL (load_to_db.py)
```

- **Data Sources**: `data_sources/online_orders.csv`, `data_sources/offline_orders.csv`.
- **Producers**: `app/producer_online.py`, `app/producer_offline.py`.
- **Broker**: RabbitMQ chạy Docker (xem `docker-compose.yml`).
- **Consumer**: `app/consumer_orders.py` đọc queue, ghi staging, áp dụng rule chất lượng dữ liệu, xuất sạch/lỗi.
- **Database**: PostgreSQL lưu trữ dữ liệu sạch từ `output/orders_clean.csv`.

### Cấu trúc thư mục

```
order_integration/
├─ docker-compose.yml
├─ Dockerfile
├─ requirements.txt
├─ README.md
├─ data_sources/
│  ├─ online_orders.csv
│  └─ offline_orders.csv
├─ staging/
├─ output/
├─ app/
│  ├─ __init__.py
│  ├─ config.py
│  ├─ logging_conf.py
│  ├─ utils.py
│  ├─ transform.py
│  ├─ validation.py
│  ├─ producer_online.py
│  ├─ producer_offline.py
│  ├─ consumer_orders.py
│  └─ load_to_db.py
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

Hoặc chạy tất cả bằng Docker:

```bash
docker compose up --build
```

RabbitMQ Management UI: http://localhost:15672 (guest/guest).
PostgreSQL: localhost:5432 (user: orders_user, pass: orders_pass, db: orders_db).

### Quy trình demo

1. Khởi động RabbitMQ + PostgreSQL (dùng compose):
   ```bash
   docker compose up rabbitmq postgres -d
   ```

2. Chạy consumer (từ thư mục gốc dự án):
   ```bash
   python -m app.consumer_orders
   ```

3. Gửi dữ liệu (trong terminal khác):
   ```bash
   python -m app.producer_online
   python -m app.producer_offline
   ```

4. Kết quả:
   - `staging/online_orders_raw.csv`, `staging/offline_orders_raw.csv`
   - `output/orders_clean.csv`
   - `output/orders_error.csv` (kèm `error_reason`)

5. Load dữ liệu sạch vào PostgreSQL:
   ```bash
   python -m app.load_to_db
   ```

### Quy tắc chất lượng dữ liệu

| Trường          | Rule                                                                 |
|-----------------|----------------------------------------------------------------------|
| `order_id`      | không rỗng                                                           |
| `customer_name` | không rỗng, không chứa chữ số, tối đa 50 ký tự                       |
| `total_amount`  | dạng số và > 0                                                       |
| `order_date`    | parse được `YYYY-MM-DD`, `DD/MM/YYYY`, `DD-MM-YYYY`                  |
| `status`        | không rỗng                                                           |

Record hợp lệ → `output/orders_clean.csv`. Record lỗi → `output/orders_error.csv` với `error_reason`.

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

Bảng `orders`:
```sql
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR(50) UNIQUE NOT NULL,
    order_date DATE NOT NULL,
    customer_id VARCHAR(50),
    customer_name VARCHAR(100) NOT NULL,
    total_amount NUMERIC(10, 2) NOT NULL,
    status VARCHAR(50),
    source VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**load_to_db.py** sử dụng UPSERT để:
- Chèn bản ghi mới
- Cập nhật bản ghi nếu `order_id` trùng

### Kiểm thử

```bash
pytest
```

### Mở rộng

- Thêm bảng khách hàng, sản phẩm hoặc enrichment khác trong `transform.py`.
- Thêm các strategy validation mới cho các business rules khác.
- Mở rộng schema PostgreSQL với indexes, foreign keys, v.v.
- Đóng gói producers vào container tương tự consumer để demo end-to-end trong Docker.

