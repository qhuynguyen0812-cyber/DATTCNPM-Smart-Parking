# Business Rules - ITS Smart Parking ALPR

## Ticket lifecycle

```txt
IN_PARKING -> COMPLETED
IN_PARKING -> NEEDS_REVIEW
IN_PARKING -> CANCELLED
NEEDS_REVIEW -> COMPLETED
NEEDS_REVIEW -> CANCELLED
```

## Entry rules

- Mỗi biển số chỉ được có một ticket đang mở.
- Ticket đang mở gồm `IN_PARKING` và `NEEDS_REVIEW`.
- Biển số phải được chuẩn hóa theo format biển số Việt Nam.
- Nếu OCR confidence thấp mà operator không nhập tay, ticket vẫn được tạo nhưng đánh dấu `review_required`.

## Exit rules

- Chỉ ticket `IN_PARKING` mới được checkout.
- Nếu biển số xe ra khớp xe vào: `COMPLETED` và `MATCH`.
- Nếu biển số xe ra không khớp: `NEEDS_REVIEW` và `MISMATCH`.
- Ticket `NEEDS_REVIEW` phải được operator/admin xử lý trước khi coi là hoàn tất.

## Review rules

- `APPROVE_EXIT`: chấp nhận xe ra dù mismatch, chuyển `COMPLETED`.
- `MARK_MATCH`: xác nhận thủ công là khớp, chuyển `COMPLETED`.
- `REJECT_EXIT`: giữ ticket ở `NEEDS_REVIEW` để tiếp tục xử lý.

## Cancel rules

- Chỉ `admin` được hủy ticket.
- Ticket đã `COMPLETED` hoặc `CANCELLED` không được hủy lại.
- Hủy ticket bắt buộc có lý do.

## Role permissions

| Action | admin | operator | viewer |
|---|---:|---:|---:|
| View logs/tickets/events | yes | yes | yes |
| Vehicle entry/exit | yes | yes | no |
| Resolve review | yes | yes | no |
| Cancel ticket | yes | no | no |
| View audit logs | yes | no | no |

## Audit and event logging

- `parking_logs`: lưu trạng thái hiện tại của ticket.
- `parking_events`: lưu event nghiệp vụ xe vào/ra/review/cancel.
- `audit_logs`: lưu hành động bảo mật/quản trị và actor thực hiện.
