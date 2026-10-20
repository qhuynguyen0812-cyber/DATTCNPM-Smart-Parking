# TRƯỜNG ĐẠI HỌC GIAO THÔNG VẬN TẢI TP. HỒ CHÍ MINH
## KHOA CÔNG NGHỆ THÔNG TIN
---
### BÁO CÁO HĐ 2 (CHƯƠNG 2): BIÊN BẢN VÀ KẾ HOẠCH LÀM VIỆC NHÓM
**Học phần**: Đồ án thực tế Công nghệ phần mềm (Capstone Project on Software Engineering)  
**Mã học phần**: 122039 | **Mã lớp học phần**: 012012213907  
**Giảng viên hướng dẫn**: Thầy Vũ Đình Long  
**Nhóm thực hiện**: Nhóm Đặng Đình Khang (STT 46 - 49)  

---

### DANH SÁCH THÀNH VIÊN VÀ PHÂN CÔNG CHUYÊN TRÁCH
| STT | Họ và tên | MSSV | Vai trò & Trọng tâm đảm nhiệm | Khối lượng phụ trách chính |
| :---: | :--- | :---: | :---: | :--- |
| 1 | **Nguyễn Quang Huy** | `034206012355` | **Tech Lead / Core Backend Engine** | **Gánh toàn bộ phần khó nhất**: Backend Architecture, API Gateway đa cổng, Pipeline AI Vision ALPR nhận diện biển số, Cổng thanh toán VietQR động 5k/10k, Bảo mật PBKDF2/JWT/RBAC và Audit Logs. |
| 2 | **Đặng Đình Khang** | `027206013096` | **Nhóm trưởng / Frontend & Algorithms** | Toàn bộ Giao diện Web Frontend (SPA) Trạm POS bảo vệ đa cổng, Thuật toán Điều phối Làn xe linh hoạt (Reversible Lane), Thuật toán Tính toán Sức chứa thời gian thực 4 Khu (A, B, C, E), và Tích hợp UI với API. |
| 3 | **Nguyễn Xuân Hoàng** | `66206000135` | **Nghiệp vụ, Kiểm thử & Báo cáo Excel** | Module Quản lý Ca trực (Shift Management) & Đối soát tiền vé theo từng cổng, Module Xử lý Sự cố mất thẻ xe (Lost Card Workflow), Viết bộ Kiểm thử tự động (Pytest), và Script xuất báo cáo Excel (.xlsx). |
| 4 | **Thạch Thị Trâm** | `51306002444` | **Báo cáo chính, CSDL & Thuyết trình** | **Chịu trách nhiệm Báo cáo chính**: Biên soạn tài liệu SRS sơ bộ và Báo cáo đồ án hoàn chỉnh chuẩn IEEE; Thiết kế Cơ sở dữ liệu (CSDL) & Vẽ sơ đồ ERD 3NF; Thiết kế Bộ Slide thuyết trình (Canva/PPT) chuyên nghiệp. |

---

## I. CHỐT ĐỀ TÀI, PHẠM VI (SCOPE) & KẾT QUẢ ĐẦU RA (DELIVERABLES)

### 1. Tên đề tài chính thức
**"Xây dựng Hệ thống Quản lý Bãi đỗ xe Thông minh Đa khu vực tại Trường Đại học Giao thông Vận tải TP.HCM Cơ sở 1 Ứng dụng AI và Thẻ RFID (Smart Campus Multi-Zone Parking Management System)"**

### 2. Lý do chọn đề tài & Tính kế thừa từ môn ITS cũ
- **Tính kế thừa**: Dự án kế thừa module AI nhận diện biển số (ALPR) từ môn Hệ thống Giao thông Thông minh (ITS) để không mất thời gian nghiên cứu lại thuật toán lõi.
- **Mở rộng theo hướng Software Engineering**:
  - Chuyển đổi từ mô hình thử nghiệm AI đơn lẻ sang một **Hệ thống Phần mềm Doanh nghiệp Đa khu vực (Enterprise Multi-Zone System)** hoàn chỉnh.
  - "May đo" chính xác theo **mặt bằng thực tế tại UTH Cơ sở 1 (Số 2 Võ Oanh, Bình Thạnh)** gồm: **4 khu đỗ xe theo thứ tự quy hoạch A - E - C - B (Tổng 2.100 xe: Sân A 250 xe, Nhà xe Khu E 600 xe, Sân C 450 xe, Đại Sân B 800 xe) và 3 cổng trạm**.
  - Khép kín toàn bộ chu trình nghiệp vụ phần mềm: Quản lý vòng đời thẻ trắng RFID UTH, kiểm soát xe vào/ra chéo cổng, tính phí đồng giá 5.000đ + phụ phí qua đêm 5.000đ, thanh toán VietQR động, và đối soát ca trực độc lập theo từng cổng.

### 3. Phạm vi dự án (Project Scope)
- **Trong phạm vi (In-Scope)**:
  - Địa điểm mục tiêu: UTH Cơ sở 1 (Số 2 Võ Oanh, Phường 25 / Thạnh Mỹ Tây, Bình Thạnh).
  - Đối tượng phương tiện: 100% xe máy (xe số, xe ga, xe điện sinh viên và cán bộ).
  - Hạ tầng cổng/làn:
    - *Cổng 1 (Võ Oanh)*: Trạm Vào gồm 4 làn quẹt thẻ song song, có chức năng gán khu đỗ để đếm chính xác sức chứa.
    - *Cổng 2 (Lối xả)*: Gồm Trạm Ra Khu C (1 trạm bốt di động gồm 2 làn song song) và Trạm Ra Khu B (4 làn).
    - *Cổng 3 (Lối xả)*: Trạm Ra Khu A & Nhà lầu E (2 làn quẹt thẻ ra).
  - Thiết bị & Bốt trạm kiểm soát: Kiosk di động khung kim loại đặt tim giữa 2 làn dưới mái che bạt tiền chế, màn hình POS chia luồng camera + Đầu đọc thẻ RFID quẹt tay + rổ thẻ UTH + khay tiền mặt + gờ giảm tốc cao su vàng-đen.
  - Định danh & Bảo mật: Thẻ trắng chỉ in logo UTH (không in số/biển số) kết hợp chip RFID bảo mật cao.
  - Chính sách phí: Cán bộ - Giảng viên - CNV (CB-GV-CNV) hoàn toàn miễn phí (0 VNĐ, barrier tự động mở khi quẹt thẻ). Sinh viên / khách vãng lai: đồng giá 5.000 VNĐ / lượt (trong ngày); gửi qua đêm phụ thu 5.000 VNĐ (tổng 10.000 VNĐ).
  - Thanh toán: Tiền mặt hoặc quét mã VietQR 5k/10k động chuẩn Napas 247.
  - Vận hành: Mở ca / đóng ca và đối soát tiền vé độc lập cho bảo vệ từng cổng.
- **Ngoài phạm vi (Out-of-Scope)**:
  - Không quản lý xe ô tô, xe tải.
  - Không thi công cơ khí rào chắn barrier vật lý ngoài trời (hệ thống xử lý ở mức tín hiệu điều khiển phần mềm/mô phỏng).

### 4. Kết quả đầu ra dự kiến (Deliverables)
1. **Phần mềm thực tế**: 
   - Web App dành cho Trạm bảo vệ (chọn cổng 1, cổng 2, cổng 3), Dashboard giám sát sức chứa 4 khu theo thời gian thực và Cổng quản trị Admin.
   - Hệ thống RESTful API (FastAPI) đáp ứng kiến trúc phân tầng, phân quyền RBAC và tài liệu Swagger OpenAPI 3.0.
   - Cơ sở dữ liệu quan hệ (SQLite/PostgreSQL) lưu trữ thẻ, vé, lịch sử vào ra và nhật ký kiểm toán.
2. **Tài liệu kỹ thuật chuẩn Công nghệ Phần mềm**:
   - Tài liệu Đặc tả Yêu cầu Phần mềm (SRS) chuẩn IEEE 830.
   - Bộ sơ đồ phân tích thiết kế hệ thống (UML: Use Case, Activity, Sequence, Class, ERD 3NF).
   - Kế hoạch và ma trận kiểm thử (Test Plan & Test Matrix).
3. **Mã nguồn & Demo**:
   - Kho mã nguồn Git chuẩn mực (nhánh main, develop, feature, commit convention).
   - Video demo kịch bản thực tế và slide thuyết trình báo cáo đồ án.

---

## II. KẾ HOẠCH VÀ PHÂN CÔNG CÔNG VIỆC (WBS)

### 1. Kế hoạch tiến độ tổng thể (4 Sprint - Mô hình Agile/Scrum)
- **Sprint 1 (Tuần 1 - 2)**: Khởi động, Khảo sát UTH CS1, Đặc tả SRS sơ bộ, Lập WBS, Thiết lập Git Workspace.
- **Sprint 2 (Tuần 3 - 4)**: Thiết kế Kiến trúc phần mềm, Thiết kế CSDL ERD 3NF đa trạm, Vẽ bộ sơ đồ UML.
- **Sprint 3 (Tuần 5 - 6)**: Hiện thực hóa Backend API, Pipeline ALPR Camera sau, Giao diện Web POS trạm bảo vệ, Tích hợp VietQR.
- **Sprint 4 (Tuần 7 - 8)**: Kiểm thử tự động (Pytest), UAT thực tế, Báo cáo đối soát doanh thu, Đóng gói sản phẩm và Báo cáo tổng kết.

### 2. Bảng Phân rã Công việc (WBS Matrix) chi tiết cho 4 thành viên (Đáp ứng Rubric A6.1)
| Mã WBS | Hạng mục công việc (Task Description) | Người phụ trách chính | Người phối hợp | Sản phẩm bàn giao (Deliverable) |
| :--- | :--- | :--- | :--- | :--- |
| **WBS 1.0** | **Khảo sát & Phân tích yêu cầu (Sprint 1)** | | | |
| 1.1 | Viết tài liệu Đặc tả SRS sơ bộ chuẩn IEEE 830 bám sát bãi xe UTH CS1 | **Thạch Thị Trâm** | Quang Huy | File `docs/SRS_SO_BO_SMART_PARKING_UTH_SE.md` |
| 1.2 | Xây dựng Bảng phân rã công việc WBS & Kế hoạch tiến độ 4 Sprint | **Đặng Đình Khang** | Cả nhóm | Biên bản & Bảng WBS Sprint 1 |
| 1.3 | Khởi tạo Git Workspace, cấu hình `.gitignore`, phân quyền cộng tác | **Nguyễn Quang Huy** | Đình Khang | Git Repository chuẩn mực |
| **WBS 2.0** | **Thiết kế phần mềm & Cơ sở dữ liệu (Sprint 2)** | | | |
| 2.1 | Thiết kế Sơ đồ Use Case tổng thể & chi tiết các trạm Cổng 1, 2, 3 | **Đặng Đình Khang** | Xuân Hoàng | Diagram Use Case |
| 2.2 | Thiết kế Cơ sở dữ liệu (CSDL) & Vẽ sơ đồ ERD chuẩn 3NF | **Thạch Thị Trâm** | Quang Huy | Sơ đồ ERD & Script Schema DB |
| 2.3 | Thiết kế Sơ đồ tuần tự (Sequence Diagram) luồng vào Cổng 1 - ra Cổng 2/3 | **Nguyễn Quang Huy** | Đình Khang | Sơ đồ Sequence |
| 2.4 | Thiết kế Wireframe/UI Mockup cho Trạm POS đa làn & Dashboard 4 khu | **Đặng Đình Khang** | Thị Trâm | Bản thiết kế giao diện Figma |
| **WBS 3.0** | **Hiện thực hóa phần mềm & Tích hợp (Sprint 3)** | | | |
| 3.1 | Tái cấu trúc Backend Service theo mô hình phân tầng chuẩn mực | **Nguyễn Quang Huy** | Đình Khang | Module `backend/` |
| 3.2 | Hiện thực hóa Core API Xe vào Cổng 1 & Xe ra Trạm B/C/AE (Khớp biển) | **Nguyễn Quang Huy** | Đình Khang | `backend/parking_service.py` |
| 3.3 | Phát triển module Tính phí đồng giá 5k & Phụ phí qua đêm 5k (Tổng 10k) | **Nguyễn Quang Huy** | Xuân Hoàng | Module tính tiền |
| 3.4 | Tích hợp dịch vụ Sinh mã VietQR 5k/10k động chuẩn Napas 247 | **Nguyễn Quang Huy** | Đình Khang | Module VietQR Payment |
| 3.5 | Tối ưu Pipeline AI Vision ALPR nhận diện biển số xe máy từ Camera sau | **Nguyễn Quang Huy** | Xuân Hoàng | `backend/alpr_service.py` |
| 3.6 | Xây dựng Thuật toán Điều phối Làn linh hoạt & Đếm sức chứa 4 khu | **Đặng Đình Khang** | Quang Huy | Thuật toán điều phối |
| 3.7 | Xây dựng toàn bộ Giao diện POS Trạm bảo vệ: Chọn cổng/làn, quét thẻ | **Đặng Đình Khang** | Quang Huy | `frontend/web/app.js` & `index.html` |
| 3.8 | Thiết kế Modal Popup hiển thị Mã VietQR 5k/10k tự động khi xe ra | **Đặng Đình Khang** | Quang Huy | Giao diện thanh toán QR |
| 3.9 | Xây dựng Dashboard Sơ đồ 4 khu hiển thị tỷ lệ lấp đầy bãi xe UTH | **Đặng Đình Khang** | Thị Trâm | Giao diện Dashboard Sức chứa |
| 3.10 | Xây dựng module Quản lý Ca trực bảo vệ & Báo cáo đối soát theo cổng | **Nguyễn Xuân Hoàng** | Quang Huy | API & Màn hình chốt ca |
| 3.11 | Xây dựng quy trình Xử lý sự cố mất thẻ xe (truy vết ảnh camera sau) | **Nguyễn Xuân Hoàng** | Quang Huy | Module xử lý mất thẻ |
| **WBS 4.0** | **Kiểm thử & Đảm bảo chất lượng (Sprint 4)** | | | |
| 4.1 | Lập Kế hoạch kiểm thử (Test Plan) & Ma trận trường hợp kiểm thử | **Thạch Thị Trâm** | Xuân Hoàng | File `docs/TEST_PLAN.md` |
| 4.2 | Viết Unit Test và Integration Test tự động bằng `pytest` (>40 test cases) | **Nguyễn Xuân Hoàng** | Quang Huy | Thư mục `tests/` |
| 4.3 | Đánh giá Benchmark độ chính xác ALPR trên tập dữ liệu xe máy UTH | **Nguyễn Xuân Hoàng** | Quang Huy | Báo cáo Benchmark Accuracy |
| 4.4 | Kiểm thử bảo mật (Phân quyền RBAC, Hash PBKDF2, Lockout brute-force) | **Nguyễn Quang Huy** | Đình Khang | Báo cáo Security Audit |
| **WBS 5.0** | **Đóng gói, Viết Báo cáo & Nghiệm thu** | | | |
| 5.1 | Đóng gói hệ thống chạy 1-click (Script `start.bat` / Docker Compose) | **Nguyễn Xuân Hoàng** | Quang Huy | File đóng gói ứng dụng |
| 5.2 | Biên soạn toàn bộ Báo cáo đồ án hoàn chỉnh (Final Report chuẩn IEEE) | **Thạch Thị Trâm** | Cả nhóm | Báo cáo đồ án cuối kỳ |
| 5.3 | Thiết kế Bộ Slide thuyết trình (Canva/PPT) chuyên nghiệp & Kịch bản | **Thạch Thị Trâm** | Cả nhóm | Slide thuyết trình & Video |

---

## III. QUY TRÌNH HOẠT ĐỘNG NHÓM (ĐÁP ỨNG RUBRIC A5.3)

Để đảm bảo hiệu quả làm việc nhóm cao nhất theo chuẩn rubric A5.3 của đề cương UTH:
1. **Phân công công việc**: Phân chia dựa trên năng lực chuyên môn của từng thành viên; mỗi task đều có 1 người phụ trách chính và 1 người phối hợp chịu trách nhiệm chéo.
2. **Quản lý & Kiểm soát tiến độ**: 
   - Họp Scrum định kỳ 2 lần/tuần (thứ Tư online lúc 20h00 và thứ Bảy offline tại trường).
   - Quản lý công việc bằng bảng Kanban trên **GitHub Projects** theo các cột: `To Do` -> `In Progress` -> `In Review` -> `Done`.
3. **Thu thập & Xử lý thông tin**: Khảo sát thực tế hiện trường UTH Cơ sở 1; ghi nhận ý kiến đóng góp từ giảng viên và các nhóm bạn trong lớp.
4. **Giải quyết xung đột & Ra quyết định**:
   - Khi có bất đồng về giải pháp kỹ thuật: Trình bày ưu/nhược điểm trong buổi họp nhóm; quyết định cuối cùng dựa trên tính khả thi thực tế và ý kiến nhóm trưởng Khang.

---

## IV. REVIEW WORKSPACE & QUY ƯỚC QUẢN TRỊ GIT (GIT WORKSPACE)

Nhóm đã khởi tạo và cấu hình workspace mã nguồn theo chuẩn công nghiệp:
- **Chiến lược phân nhánh (Branching Strategy)**:
  - `main`: Nhánh ổn định, chỉ chứa code đã qua kiểm thử và được giảng viên nghiệm thu.
  - `develop`: Nhánh tích hợp chính.
  - `feature/<task-name>`: Nhánh phát triển tính năng riêng của từng thành viên (ví dụ: `feature/gate-management`, `feature/vietqr-modal`).
- **Quy ước đặt tên Commit (Conventional Commits)**:
  - `feat:` Thêm tính năng mới (VD: `feat: implement multi-zone capacity counter`).
  - `fix:` Sửa lỗi (VD: `fix: handle 2-line license plate regex`).
  - `docs:` Tài liệu hóa (VD: `docs: complete syllabus-aligned SRS and WBS`).
  - `refactor:` Tái cấu trúc mã nguồn (VD: `refactor: modularize gate routing service`).
  - `test:` Bổ sung kiểm thử tự động (VD: `test: add unit test for overnight surcharge`).

---

## V. CÁC CÂU HỎI TRAO ĐỔI VỚI GIẢNG VIÊN VŨ ĐÌNH LONG

Trong buổi review tuần tới, nhóm dự kiến trao đổi với Thầy Long 3 vấn đề chuyên môn:
1. *"Thưa Thầy, từ đề tài ITS cũ, nhóm em đã mở rộng mô hình bãi xe bám sát mặt bằng thực tế của UTH Cơ sở 1 gồm 4 khu (A, B, C, E) và 3 cổng (8 làn xe) với cơ chế đồng bộ đa trạm. Thầy nhận xét về hướng tiếp cận mở rộng theo cấu trúc thực tế này của nhóm đã đáp ứng đúng kỳ vọng của đồ án Capstone SE chưa ạ?"*
2. *"Thưa Thầy, về quy trình kiểm thử chất lượng phần mềm, Thầy có yêu cầu nhóm triển khai tự động hóa CI/CD trên GitHub Actions để chạy bộ test `pytest` mỗi khi tạo Pull Request ngay từ Sprint 2 không ạ?"*
3. *"Thưa Thầy, đối với nghiệp vụ phụ phí gửi xe qua đêm (5k vé lượt + 5k phụ phí = 10k), nhóm thiết lập mốc chuyển ca đêm là 23h00 thì đã phù hợp với thực tế khuôn viên trường chưa ạ?"*

---
*Biên bản được lập và thông qua bởi toàn thể 4 thành viên Nhóm Đặng Đình Khang.*  
**Nhóm trưởng ký tên**: *Đặng Đình Khang*
