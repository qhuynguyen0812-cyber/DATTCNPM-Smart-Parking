# Production Candidate Plan for ITS

## Mục tiêu
Chuyển ITS từ prototype demo sang production-candidate theo từng lớp, không phá flow hiện tại.

## 1. Auth thật
### Hiện trạng
- API dùng `x-api-token` tĩnh
- không có user model, role, session, refresh token

### Production-candidate direction
- thêm user store và role-based access
- dùng JWT access token + refresh token
- phân tách role tối thiểu:
  - `admin`
  - `operator`
  - `viewer`
- tách secret khỏi source code, dùng env/secret manager

## 2. Monitoring và observability
### Hiện trạng
- có file log cơ bản
- chưa có request id, health metrics, latency tracking

### Production-candidate direction
- thêm structured logging JSON
- thêm request id / correlation id
- thêm metrics endpoint kiểu Prometheus
- thêm event log cho:
  - OCR request
  - vehicle entry
  - vehicle exit
  - mismatch
  - OCR fail

## 3. Camera ingestion
### Hiện trạng
- upload ảnh thủ công
- chưa có streaming/live feed

### Production-candidate direction
- tách camera ingestion service riêng
- hỗ trợ nguồn:
  - RTSP camera
  - webcam
  - folder watcher
- pipeline đề xuất:
  1. camera source
  2. frame sampler
  3. detector/ocr worker
  4. event bus / queue
  5. parking decision service

## 4. Runtime/web app
### Hiện trạng
- Streamlit phù hợp demo
- khó mở rộng multi-user và realtime

### Production-candidate direction
- giữ Streamlit cho demo/internal QA
- production UI nên chuyển sang web app chuẩn:
  - FastAPI backend
  - frontend riêng như React / Next.js / Vue
- API trở thành source of truth, không để UI giữ business logic

## 5. DB và persistence
### Hiện trạng
- SQLite đủ cho prototype

### Production-candidate direction
- chuyển sang PostgreSQL
- thêm migration tool chuẩn như Alembic
- thêm bảng:
  - users
  - roles
  - audit_logs
  - camera_sources
  - ocr_events
  - system_events

## 6. OCR hard-case roadmap
### Nhóm fail chính hiện tại
- top-only / partial read
- numeric-only garbage
- weak crop / unreadable frame
- ambiguous top line như `T0A99999`

### Hướng xử lý
- detector fallback model
- crop retry strategy với nhiều margin khác nhau
- retry OCR trên rotated / sharpened / denoised plate crop
- phân loại hard-case để buộc manual verification

## 7. Triển khai theo phase
### Phase A
- giữ prototype ổn định
- benchmark có ground truth
- cải thiện hard-case OCR

### Phase B
- API-first backend
- auth thật
- event logging
- camera ingestion stub

### Phase C
- web UI production
- PostgreSQL
- metrics/monitoring
- deployment và vận hành thực tế
