# ITS Application Requirements

## Domain

Smart Parking / Parking Access Control / Vehicle Identification.

## Problem statement

Bãi giữ xe thủ công dễ ghi sai biển số, khó truy vết khi tranh chấp, và mất thời gian khi xe vào/ra. Hệ thống cần dùng camera như một detector sensor để nhận diện biển số, hỗ trợ operator ra quyết định, lưu event và audit phục vụ vận hành.

## ITS model

```txt
Camera/Image Sensor
-> Detection/OCR Processing
-> Plate Normalization + Quality Assessment
-> Operator Decision Support
-> Entry/Exit Business Logic
-> Event/Audit Logging
```

## Functional requirements

| ID | Requirement |
|---|---|
| FR1 | Nhận ảnh xe vào/ra từ UI hoặc API |
| FR2 | Detect/OCR biển số từ ảnh |
| FR3 | Chuẩn hóa biển số Việt Nam |
| FR4 | Tạo ticket xe vào |
| FR5 | Chặn trùng biển số đang có ticket mở |
| FR6 | Xử lý xe ra theo ticket |
| FR7 | Đối chiếu biển số vào/ra |
| FR8 | Đánh dấu review khi mismatch hoặc OCR confidence thấp |
| FR9 | Cho operator/admin resolve ticket cần review |
| FR10 | Cho admin hủy ticket có lý do |
| FR11 | Lưu parking event và audit log |
| FR12 | Cung cấp API phân quyền theo role |

## Non-functional requirements

| ID | Requirement |
|---|---|
| NFR1 | Không expose internal filesystem paths mặc định |
| NFR2 | API write routes phải yêu cầu bearer token role phù hợp |
| NFR3 | Có rate limit cơ bản cho write routes |
| NFR4 | Password user nội bộ phải hash bằng PBKDF2 |
| NFR5 | Có lockout sau nhiều lần login sai |
| NFR6 | SQLite schema migration phải backward-compatible |
| NFR7 | Có test cho nghiệp vụ chính và security rules |

## Actors

| Actor | Role |
|---|---|
| Driver | Đưa xe vào/ra bãi |
| Camera sensor | Cung cấp ảnh đầu vào |
| Operator | Xác nhận xe vào/ra, resolve mismatch |
| Admin | Quản trị, hủy ticket, xem audit |
| Viewer | Chỉ xem logs/tickets |

## Measurable metrics

- OCR exact-match accuracy.
- Manual correction rate.
- Mismatch rate.
- Average processing latency.
- Number of tickets requiring review.
- Failed login count / lockout events.
