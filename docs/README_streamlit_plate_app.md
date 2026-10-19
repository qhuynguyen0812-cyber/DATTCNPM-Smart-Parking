# Streamlit UI, ứng dụng nhận diện biển số xe

## Mục tiêu
Đây là giao diện demo cho bài toán kiểm soát xe máy ra vào bằng nhận diện biển số Việt Nam.

UI được thiết kế theo hướng:
- ít thao tác
- dễ trình bày trước hội đồng
- cho phép xem nhanh ảnh gốc, ảnh nhận diện, kết quả OCR và mã vé
- hỗ trợ fallback nhập tay khi OCR chưa đáng tin

## Luồng chính
### Xe vào
1. Tải ảnh biển số hoặc ảnh xe
2. Hệ thống detect + OCR + hậu xử lý biển số Việt Nam
3. Hiển thị mức độ tin cậy và cảnh báo chất lượng OCR
4. Người dùng có thể chỉnh tay biển số nếu cần
5. Xác nhận để tạo vé xe

### Xe ra
1. Chọn vé đang hoạt động
2. Tải ảnh biển số xe ra
3. Hệ thống detect + OCR + hậu xử lý
4. Người dùng kiểm tra kết quả và chỉnh tay nếu cần
5. Xác nhận xe ra và đối chiếu biển số vào/ra

### Nhật ký
- Xem toàn bộ lịch sử vé
- Theo dõi trạng thái xe trong bãi hoặc đã hoàn tất
- Theo dõi kết quả match/mismatch

## Điểm mạnh của UI hiện tại
- Gọn, dễ demo
- Có trạng thái xe vào, xe ra, nhật ký rõ ràng
- Có preview ảnh gốc và ảnh annotate
- Có cảnh báo OCR usable / chưa usable
- Có vùng hiển thị mã vé rõ ràng

## Giới hạn
- Chưa phải giao diện vận hành chuyên nghiệp cho nhiều nhân viên cùng lúc
- Chưa có luồng realtime từ camera live
- Chưa có quyền người dùng, audit chi tiết, hoặc phân lane

## Cách chạy
```bash
streamlit run frontend/app.py
```

## Ghi chú trình bày demo
Khi demo, nên nói rõ:
- AI hỗ trợ nhận diện tự động
- hệ thống có cơ chế kiểm tra thủ công nếu OCR chưa chắc
- điểm mạnh nằm ở flow nghiệp vụ và hậu xử lý biển số Việt Nam, không chỉ ở model OCR thô
