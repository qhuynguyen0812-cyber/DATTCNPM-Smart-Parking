# GO TO MARKET PLAN - ITS / Parking ALPR

## Mục tiêu thực tế
Đưa hệ thống từ mức **prototype tốt / đồ án mạnh** lên mức:
1. **Pilot nội bộ có người dùng thật**
2. **Triển khai thương mại quy mô nhỏ**
3. **Sẵn sàng mở rộng thêm site / khách hàng**

---

## Đánh giá thẳng hiện trạng
Hiện tại hệ thống **chưa sẵn sàng ra thị trường ngay** theo nghĩa production thương mại.

Điểm mạnh hiện có:
- Luồng nghiệp vụ xe vào / xe ra đã rõ
- Có human-in-the-loop, không phụ thuộc OCR mù quáng
- Có logging, ticketing, match/mismatch
- Có UI thao tác được
- Có test coverage tương đối ổn
- Đã có nhiều bước hardening hơn mặt bằng prototype

Điểm chặn lớn trước khi bán/triển khai thật:
- Auth còn ở mức prototype
- Chưa có audit log đầy đủ cho hành động người dùng
- Chưa có backup/restore/ops story rõ ràng
- Chưa có đóng gói triển khai chuẩn
- OCR chưa benchmark đủ trên dữ liệu vận hành thật
- Chưa có observability / metrics / failure alert đủ để support ngoài hiện trường
- Chưa có readiness cho môi trường nhiều người dùng / nhiều site

---

## Chiến lược ra thị trường đúng
Không đi thẳng từ prototype -> production diện rộng.

Lộ trình đúng:

### Giai đoạn 1 - Pilot nội bộ / khách hàng đầu tiên
Mục tiêu:
- 1 bãi xe nhỏ
- số user ít
- có người vận hành được đào tạo
- chấp nhận human review

### Giai đoạn 2 - Commercial small rollout
Mục tiêu:
- 2-5 điểm triển khai
- có quy trình support
- có backup / monitoring / update path

### Giai đoạn 3 - Scale / product hóa
Mục tiêu:
- multi-site
- auth chuẩn hơn
- metrics / audit / support / SLA rõ ràng

---

## P0 - Những việc bắt buộc trước pilot thật

### 1. Đóng băng chế độ vận hành thực tế
Cần chốt rõ hệ thống sẽ bán theo mode nào:
- Đây là **manual operator workflow**
- Không quảng bá như hệ thống fully autonomous
- OCR là công cụ hỗ trợ, operator vẫn có quyền xác nhận cuối

Nếu không chốt điểm này, kỳ vọng khách hàng sẽ lệch và dễ vỡ dự án.

### 2. Làm rõ deployment profile
Cần có một profile triển khai chuẩn:
- Python version cố định
- dependency lock
- biến môi trường mẫu hoàn chỉnh
- thư mục data/log/report rõ ràng
- script start app / start api / smoke check

### 3. Chốt OCR profile dùng thật
Hiện nên triển khai theo 2 mode:
- **Nhanh nhất**: dùng hằng ngày
- **Chính xác nhất**: dùng khi ảnh khó

Trước pilot phải benchmark tối thiểu:
- tốc độ trung bình mỗi lượt quét
- tỷ lệ phải sửa tay
- tỷ lệ mismatch giả
- hiệu quả theo từng profile OCR

### 4. Backup / restore
Tối thiểu phải có:
- backup SQLite theo lịch
- backup uploads/logs
- quy trình restore thử nghiệm được

Nếu không có bước này thì mất DB là coi như mất lịch sử vận hành.

### 5. Audit log người dùng
Phải ghi được:
- ai xác nhận xe vào
- ai xác nhận xe ra
- ai sửa tay biển số
- ai đổi role / khóa user / xóa user
- khi nào thao tác xảy ra

Hiện logging nghiệp vụ đã có, nhưng audit user action chưa đủ chuẩn để đi pilot thật.

### 6. Hardening auth mức tối thiểu
Cho pilot nhỏ có thể chưa cần JWT đầy đủ, nhưng tối thiểu cần:
- password policy rõ hơn
- lockout/login controls
- không dùng shared account giữa nhiều nhân viên
- tách rõ operator/admin
- review lại password reset/change flow

---

## P1 - Những việc nên làm trước khi bán thương mại

### 1. Packaging triển khai
Ít nhất nên có một trong các cách triển khai chuẩn:
- Docker Compose
- script bootstrap production
- Windows service setup guide nếu target khách hàng là Windows PC

### 2. Monitoring cơ bản
Cần biết hệ thống có sống hay chết:
- health check thật
- metrics cơ bản
- log rotation
- alert khi app/API chết
- alert khi OCR lỗi hàng loạt

### 3. Data retention policy
Cần quy định rõ:
- giữ ảnh bao lâu
- giữ log bao lâu
- ảnh nào được xóa
- quyền truy cập ảnh/log

### 4. Error handling thân thiện với vận hành
Cần có thông báo kiểu vận hành:
- lỗi OCR
- lỗi DB
- lỗi file ảnh
- lỗi ticket không hợp lệ
- lỗi thiếu model/runtime

và nên có hướng dẫn thao tác tiếp theo cho operator.

### 5. Nhật ký / báo cáo vận hành
Nên có export/report tối thiểu:
- tổng xe vào/ra theo ngày
- mismatch count
- số ca sửa tay
- hiệu quả OCR theo profile

---

## P2 - Những việc cần để scale thật sự

### 1. Thay SQLite khi vượt tải nhẹ
Nếu nhiều user/site hơn:
- chuyển PostgreSQL
- migration rõ ràng
- backup chuẩn hơn

### 2. Auth production-grade
Khi đi xa hơn pilot:
- session/JWT
- permission model chuẩn
- audit trail đầy đủ
- secret rotation

### 3. Multi-site support
Nếu triển khai nhiều bãi:
- site id
- phân quyền theo site
- filter log theo site
- cấu hình detector/OCR riêng cho từng site

### 4. Remote support / update path
Cần có cách:
- update phiên bản an toàn
- rollback nhanh
- kiểm tra cấu hình từ xa

---

## Đề xuất thương mại hóa thực tế

### Thông điệp bán đúng
Nên bán như:
- hệ thống hỗ trợ kiểm soát xe ra vào bằng AI nhận diện biển số
- có operator review để tăng độ an toàn
- tối ưu cho bãi xe cần bán tự động hoàn toàn 100%

Không nên bán như:
- AI nhận diện tuyệt đối chính xác trong mọi điều kiện
- hệ thống thay thế hoàn toàn con người

### Gói triển khai hợp lý ban đầu
Giai đoạn đầu nên bán/triển khai dạng:
- on-premise trên 1 máy vận hành
- 1-3 user nội bộ
- 1 bãi xe nhỏ hoặc pilot 1 site
- có training operator
- có checklist vận hành mỗi ngày

---

## Checklist chấp nhận trước pilot
Chỉ nên pilot thật khi đạt đủ:
- [ ] App/UI ổn định sau restart và đổi config
- [ ] OCR profile nhanh + chính xác hoạt động ổn định
- [ ] Có benchmark trên ảnh thật của bãi xe mục tiêu
- [ ] Có backup/restore test qua ít nhất 1 lần
- [ ] Có audit log cho hành động operator/admin
- [ ] Có hướng dẫn cài đặt và vận hành
- [ ] Có quy trình xử lý lỗi thường gặp
- [ ] Có 1 bộ smoke test sau triển khai

---

## Checklist chấp nhận trước commercial rollout
- [ ] Monitoring cơ bản hoạt động
- [ ] Log rotation / retention rõ ràng
- [ ] Deployment guide chuẩn hóa
- [ ] Cấu hình môi trường được kiểm soát
- [ ] OCR được benchmark theo site thực tế
- [ ] Admin/auth không còn ở mức prototype đơn giản
- [ ] Có quy trình update/rollback

---

## Việc nên làm ngay tiếp theo trong repo này
Ưu tiên thực dụng:
1. Thêm audit log cho hành động operator/admin
2. Thêm export/report cho logs vận hành
3. Tạo deployment profile chuẩn (env + startup + smoke)
4. Thêm backup script cho DB + uploads
5. Benchmark trên bộ ảnh thực tế của bãi xe mục tiêu
6. Làm docs triển khai pilot từng bước

---

## Kết luận
Nếu hỏi thẳng: **hệ thống này đã đủ để đem đi demo, chào pilot, và thử nghiệm khách hàng đầu tiên**.

Nhưng để nói là **đưa ra thị trường nghiêm túc** thì cần hoàn thành ít nhất P0 và phần lớn P1.

Hướng đúng không phải là cố vẽ repo thành “đã production”, mà là:
- chốt định vị sản phẩm đúng
- pilot nhỏ thật chắc
- đo dữ liệu thật
- rồi mới scale.
