# Streamlit UI - Ứng dụng nhận diện biển số xe

## Trạng thái hiện tại
Bản này đã được nâng cấp từ demo nhóm lên mức **prototype hoàn chỉnh hơn**:
- Giao diện Streamlit cho xe vào / xe ra / xem dữ liệu
- Detection biển số bằng YOLO
- OCR biển số bằng EasyOCR
- Lưu dữ liệu vào SQLite
- Đối chiếu biển số lúc xe vào và xe ra
- Lưu đường dẫn ảnh gốc / ảnh detect / ảnh crop
- Cho phép nhập tay biển số như cơ chế fallback khi OCR đọc sai

## Chức năng chính
- Upload ảnh xe hoặc ảnh biển số
- Tự động detect vùng biển số
- Tự động OCR ký tự trên biển số
- Ghi nhận xe vào với mã vé tự sinh
- Xử lý xe ra bằng mã vé
- So khớp biển số vào / ra
- Xem lịch sử xử lý và xuất CSV

## Cài đặt
```bash
pip install -r requirements_streamlit.txt
```

## Chạy ứng dụng
```bash
streamlit run license_plate_app.py
```

## Cấu trúc dữ liệu
Bảng `parking_logs` gồm:
- `ticket_id`
- `plate_entry`
- `plate_exit`
- `entry_time`
- `exit_time`
- `status`
- `match_result`
- `entry_image_path`
- `entry_detected_path`
- `entry_plate_path`
- `exit_image_path`
- `exit_detected_path`
- `exit_plate_path`
- `ocr_confidence`

## Lưu ý
- Nếu máy chưa có đủ dependency, app sẽ báo rõ detection/OCR chưa dùng được.
- Nếu OCR đọc sai, có thể nhập tay biển số để tiếp tục demo.
- Đây vẫn là **prototype học thuật**, chưa phải bản production.

## Hướng nâng cấp tiếp theo
- Tích hợp webcam/camera live
- Tối ưu OCR theo format biển số Việt Nam
- Thêm đánh giá accuracy trên bộ ảnh test
- Nâng cấp DB/backend nếu cần nhiều người dùng
- Tích hợp camera IP / barrier / API
