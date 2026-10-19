# ITS, Hệ thống nhận diện biển số xe máy

Prototype kiểm soát xe ra vào bằng biển số xe máy Việt Nam, tối ưu cho demo học thuật nhưng có cấu trúc đủ rõ để tiếp tục nâng cấp.

## Dự án đang làm được gì
- Ghi nhận xe vào, xe ra, đối chiếu biển số theo mã vé
- Nhận diện biển số từ ảnh bằng detector + EasyOCR
- OCR ưu tiên bằng AI Vision (9Router / cx/gpt-6-sol) với human-in-the-loop, local OCR là fallback
- Hậu xử lý biển số Việt Nam, đặc biệt cho biển xe máy 1 dòng và 2 dòng
- Đánh giá chất lượng OCR để cảnh báo khi kết quả chưa đủ tin cậy
- Cho phép nhập tay biển số để cứu flow khi OCR chưa ổn
- Lưu nhật ký xử lý, sự kiện và audit log vào SQLite
- Có API FastAPI để tích hợp cơ bản
- Có script benchmark để đo hiệu quả OCR trên bộ ảnh gán nhãn
- Giao diện pixel (VT323/Press Start 2P) phong cách lofi chill: mặt trời động, mây trôi, sao lấp lánh, bóng bãi giữ xe
- Đăng nhập có captcha chống tự động hoá
- Dashboard và báo cáo dùng dữ liệu thật từ database, không giả lập số liệu

## Kiến trúc hiện tại
```text
its/
├── api/                  # FastAPI cho OCR và vehicle entry/exit
├── backend/              # Nghiệp vụ, OCR, DB, validation, storage
├── data/                 # Dataset, benchmark results, sample images
│   ├── benchmark/        # datasets, ground_truth, results, review
│   └── samples/          # ảnh mẫu / ảnh review phục vụ demo và benchmark
├── docs/                 # Ghi chú dự án, báo cáo, kế hoạch triển khai
├── frontend/             # Web UI (SPA HTML/CSS/JS)
├── integrations/         # Mã tham chiếu / detector từ nguồn ngoài
├── models/external/      # Detector YOLO thay thế (.pt)
├── scripts/              # Benchmark, compare, smoke utilities
├── tests/                # Unit tests cho logic lõi
├── requirements_web.txt
└── README.md
```

## Thành phần chính
### 1. Frontend
- `frontend/web/`: giao diện web chính (SPA HTML/CSS/JS, FastAPI phục vụ tại `/`)
- `frontend/app.py` + `frontend/ui.py`: UI Streamlit cũ (không còn là giao diện mặc định)

### 2. Backend
- `backend/alpr_service.py`: OCR pipeline, chấm điểm candidate, format biển số VN
- `backend/app_service.py`: orchestration layer cho UI và API
- `backend/parking_service.py`: nghiệp vụ tạo vé, xe vào, xe ra, match/mismatch
- `backend/plate_format.py`: normalize và format biển số Việt Nam
- `backend/ocr_quality.py`: đánh giá kết quả OCR có usable hay không
- `backend/db.py`: SQLite schema và truy vấn đơn giản
- `backend/storage.py`: lưu file upload và ảnh annotate
- `backend/validators.py`: validate input

### 3. API
- `api/main.py`
- endpoints chính:
  - `GET /health`
  - `GET /logs`
  - `GET /tickets/active`
  - `POST /ocr`
  - `POST /vehicle/entry`
  - `POST /vehicle/exit`

## Cài đặt
Yêu cầu:
- Python 3.11+

Cài dependency:
```bash
pip install -r requirements_streamlit.txt
```

Tùy chọn cấu hình môi trường:
```bash
copy .env.example .env
```

## Chạy ứng dụng (web)
Cách nhanh nhất: double-click `start.bat` (tự cài thư viện + seed tài khoản demo + mở trình duyệt).

Hoặc chạy thủ công:
```bash
python scripts/seed_demo_users.py   # tài khoản demo: admin / ItsDemo@2026A
uvicorn api.main:app --host 0.0.0.0 --port 8000
```
Mở `http://localhost:8000`. FastAPI vừa phục vụ API vừa phục vụ giao diện web (SPA) tại `/`.

Trong **Xe vào** hoặc **Xe ra**, chọn **Mở camera** để dùng webcam/USB hoặc camera sau điện thoại. Cấp quyền camera, chọn thiết bị nếu có nhiều camera, rồi **Chụp ảnh → Quét biển số**. Ảnh chụp được kiểm tra cùng giới hạn JPG/PNG/WEBP, tối đa 10 MB, như ảnh tải lên. Quét hiển thị biển số để đối chiếu; người vận hành vẫn phải bấm tạo vé hoặc xác nhận xe ra. Camera tự tắt sau khi chụp, đóng, đổi trang hoặc đưa ứng dụng xuống nền.

Camera trực tiếp cần HTTPS hoặc `localhost` và quyền truy cập của trình duyệt ([tài liệu getUserMedia](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia)). Nút **Camera điện thoại** mở trình chụp ảnh của thiết bị nếu trình duyệt hỗ trợ; có thể dùng cách này khi không có xem trực tiếp. Camera IP/RTSP tiếp tục cần cấu hình thiết bị riêng, không dùng webcam của trình duyệt làm bằng chứng rằng tích hợp phần cứng đã sẵn sàng.

## Chạy API riêng
```bash
uvicorn api.main:app --reload
```

## Dữ liệu runtime
Mặc định dữ liệu được lưu tại:
- `~/plate_demo_data/parking_system.db`
- `~/plate_demo_data/uploads/`
- `~/plate_demo_data/logs/`

Có thể đổi bằng biến môi trường:
- `ITS_BASE_DIR`
- `ITS_DB_NAME`
- `ITS_UPLOAD_DIR`
- `ITS_API_TOKEN`
- `ITS_API_BEARER_ADMIN_TOKEN`
- `ITS_API_BEARER_OPERATOR_TOKEN`
- `ITS_API_BEARER_VIEWER_TOKEN`
- `ITS_API_EXPOSE_INTERNAL_PATHS`
- `ITS_FAST_MODE`

## Ghi chú bảo mật hiện tại
- Không còn default API token hoặc default password an toàn giả tạo trong runtime.
- Streamlit UI dùng tài khoản username/password nội bộ; đây là lớp auth riêng cho giao diện vận hành.
- Muốn bật API protected routes bằng token tĩnh, bạn phải cấu hình `ITS_API_TOKEN`.
- API read routes chấp nhận **một trong hai**: `x-api-token` hoặc bearer role token hợp lệ.
- API write routes yêu cầu bearer role token; `viewer` chỉ nên có quyền xem, `admin` và `operator` mới được thao tác xe vào/ra ở API layer.
- Mặc định API **không** expose raw internal filesystem paths; chỉ bật lại nếu thật sự cần bằng `ITS_API_EXPOSE_INTERNAL_PATHS=true`.

## Benchmark và kiểm thử
Kiểm tra cấu hình cục bộ:
```bash
python scripts/bootstrap.py doctor
```

Ví dụ chạy nhanh:
```bash
python scripts/bootstrap.py test
python scripts/bootstrap.py api
python scripts/bootstrap.py app
python scripts/bootstrap.py benchmark
python scripts/bootstrap.py compare-ocr
python scripts/bootstrap.py prepare-ground-truth
python scripts/bootstrap.py backup
```

Ví dụ benchmark:
```bash
python scripts/run_benchmark_dataset.py
python scripts/benchmark_bad_cases.py
python scripts/benchmark_with_ground_truth.py
python scripts/generate_benchmark_candidates.py
python scripts/compare_ocr_engines.py
python scripts/prepare_ground_truth_dataset.py
```

Quy ước benchmark hiện tại:
- Dataset và ground truth nằm trong `data/benchmark/datasets/` và `data/benchmark/ground_truth/`
- Kết quả benchmark sinh ra trong `data/benchmark/results/`
- File review/candidate nằm trong `data/benchmark/review/`
- `run_benchmark_dataset.py` đo **production flow** qua `process_plate_image()`
- `benchmark_bad_cases.py` đo **production flow** cho subset `label=bad`
- `benchmark_with_ground_truth.py` đo **baseline OCR engine** qua `run_alpr()` với ground truth template
- `compare_ocr_engines.py` đo **engine comparison** ở mức `run_alpr()`
- `generate_benchmark_candidates.py` chỉ tạo candidate CSV để review/gán nhãn, **không** chạy benchmark

Ví dụ chạy test:
```bash
pytest tests -q
```

Bộ test hiện cover:
- validator và format biển số
- đánh giá chất lượng OCR
- nghiệp vụ app service và parking service
- API contract cơ bản
- schema migration và index SQLite

Chạy toàn bộ kiểm tra backend và giao diện bằng một lệnh trên Windows:

```powershell
py -3 scripts/run_checks.py
```

Kết quả ngày 13/10/2026: **247 kiểm tra backend và 19 kiểm tra giao diện đạt**.
Kiểm thử dùng cơ sở dữ liệu tạm riêng, không ghi vào dữ liệu vận hành.
Để chạy thêm 12 tình huống ảnh mẫu qua provider AI đang cấu hình:

```powershell
py -3 scripts/run_checks.py --live-vision
```

Tùy chọn này gọi API thật và tiêu thụ lượt sử dụng; chỉ gửi ảnh mô phỏng do script
tạo, không tạo vé xe. Kết quả ảnh mô phỏng không đại diện độ chính xác ngoài thực tế.

## Backup runtime
Để backup nhanh dữ liệu pilot / demo hiện tại:
```bash
python scripts/bootstrap.py backup
# hoặc
python scripts/backup_runtime.py
```

Backup sẽ tạo file `.zip` trong thư mục:
- `~/plate_demo_data/backups/`

Nội dung gồm:
- SQLite DB hiện tại
- toàn bộ thư mục uploads
- `manifest.json` để ghi metadata backup

## Giới hạn hiện tại
- Đây vẫn là prototype, chưa phải production system
- OCR còn yếu với ảnh khó, biển dọc, góc chụp xấu, crop lệch
- Streamlit phù hợp demo hơn là vận hành đa người dùng
- SQLite chỉ hợp với tải nhẹ
- API hiện mới ở mức tích hợp cơ bản; auth đã bớt rời rạc hơn nhưng vẫn chưa đạt chuẩn production (chưa có session/JWT, rate limit, secret rotation)
- Logs API hiện có pagination cơ bản và filter nhẹ, nhưng chưa phải query contract production-grade
- Các script benchmark chính hiện đã dùng path repo-relative/config-driven; tuy vậy chất lượng benchmark vẫn phụ thuộc ground truth dataset và naming discipline
- PaddleOCR chỉ nên bật sau khi benchmark thật, không nên thêm phức tạp chỉ vì nghe có vẻ mạnh hơn
- Exact-match benchmark chỉ có ý nghĩa khi `data/benchmark/datasets/benchmark_dataset.csv` đã được gán `expected_plate` đúng

## Định vị đúng của dự án
Dự án này nên được trình bày là:
- hệ thống hỗ trợ kiểm soát xe ra vào có AI nhận diện biển số
- có human-in-the-loop khi OCR chưa chắc chắn
- có logging và đối chiếu để phục vụ demo nghiệp vụ thực tế

Không nên trình bày như một hệ thống fully autonomous độ chính xác cao trong mọi điều kiện.

## Lộ trình pilot / thương mại hóa
Nếu mục tiêu là đưa hệ thống đi pilot hoặc triển khai thương mại quy mô nhỏ, xem thêm:
- `docs/GO_TO_MARKET_PLAN_2026-04-20.md`

Tài liệu này chia rõ:
- mức sẵn sàng hiện tại
- các việc bắt buộc trước pilot thật
- các việc nên làm trước commercial rollout
- checklist vận hành và triển khai
