# Báo cáo kiểm thử và cải tiến ITS — 06/09/2026

Mã nguồn được sửa trực tiếp tại thư mục dự án người dùng cung cấp. Các phép thử dùng runtime riêng trong workspace, không dùng database vận hành mặc định.

## Kết quả kiểm chứng

| Hạng mục | Kết quả | Giới hạn |
|---|---|---|
| Toàn bộ bộ test chính `tests/` | 190 đạt, 0 lỗi, 34 cảnh báo; 14,31 giây | Nhiều test OCR dùng mock; không phải 190 thử nghiệm nhận diện ảnh thật |
| Giao diện Streamlit AppTest | Đăng nhập, Dashboard, Xe vào, Xe ra, Cần kiểm tra, Nhật ký, Tài khoản: không exception | Kiểm thử dựng màn hình; chưa đo thao tác camera vật lý hoặc mọi thao tác trình duyệt |
| Đồng thời cấp vé | 8 yêu cầu cùng biển số chỉ tạo 1 vé | Kiểm thử SQLite trên một máy |
| API performance smoke | 90 request đều HTTP 200 | TestClient trong tiến trình, không phải tải mạng/production |
| `/health` | Trung bình 2,51 ms; p95 2,93 ms | 30 request |
| `/readiness` | Trung bình 3,89 ms; p95 4,63 ms | 30 request |
| `/system/scorecard` | Trung bình 2,23 ms; p95 2,80 ms | 30 request |
| OCR thực bằng EasyOCR | 0/2 ảnh khớp nhãn sau đối chiếu | Hai ảnh ô tô khó, đã annotate; không đại diện xe máy thực tế |
| Production check | 2 FAIL: JWT mặc định/quá ngắn và hardware mô phỏng | Kết quả cấu hình kiểm thử; chưa kiểm chứng thiết bị thật |

## Những gì đã cải tiến

1. Dashboard bỏ accuracy 98,65%, tăng trưởng cố định, biểu đồ tự tạo, camera LIVE giả và hoạt động mẫu khi database trống. Lượt vào/ra hôm nay tính từ thời gian nhật ký; xe còn trong bãi gồm cả vé cần kiểm tra; confidence lấy từ bản ghi.
2. API scorecard bỏ điểm cố định 9–10/10. Điểm chưa đo trả null; client tích hợp cần xử lý giá trị này.
3. Readiness đọc bảng database thật bằng kết nối read-only; thiếu database/schema trả 503 và không tự tạo file để làm phép kiểm tra thành công.
4. Các thao tác vé khóa giao dịch đọc–kiểm tra–ghi bằng BEGIN IMMEDIATE, tránh hai yêu cầu cùng vượt qua kiểm tra trùng biển số hoặc ghi đè chuyển trạng thái.
5. Tài khoản database xác thực thất bại không quay về dùng mật khẩu cấu hình cũ. Đã bổ sung test chống hồi quy.
6. Confidence NaN/vô cực/không hợp lệ không được nâng thành OCR đáng tin. Thông báo đổi thành “Đúng định dạng, cần đối chiếu ảnh”.
7. Production check thử ghi rồi rollback, thay vì SELECT 1 để tuyên bố database ghi được. Cấu hình endpoint không đủ để cho hardware PASS. CV inventory không tự gọi là field-ready.
8. Sửa cách khởi động TestClient cho test API và công cụ performance; lưu requirements_test.txt với phiên bản đã chạy.
9. Sửa đúng hai nhãn đã nhìn ảnh trong dataset và bản prefilled: 30-F 513.15; 60-A 999.99. Không tự sửa các ảnh khác chưa đối chiếu.

## OCR thực: bằng chứng và hạn chế

- Ảnh thứ nhất: đáp án 30-F 513.15, dự đoán 13-DF 613.15, confidence 97,4%. Đây là ví dụ cụ thể confidence cao vẫn sai.
- Ảnh thứ hai: đáp án 60-A 999.99, dự đoán T99999, confidence 62,1%.
- Lần đầu khoảng 15,1 giây có khởi tạo/tải model; ảnh thứ hai khoảng 0,743 giây. Không dùng trung bình hai lần này để tuyên bố tốc độ vận hành.
- Chưa thử dịch vụ Vision/9Router do môi trường không có cấu hình dịch vụ hoạt động; chưa thử PaddleOCR hay phần cứng thật.
- Chưa có bằng chứng rằng độ chính xác OCR đã tăng. Cải tiến đã kiểm chứng tập trung vào tính đúng của dữ liệu hiển thị, đánh giá, đăng nhập và tính nhất quán giao dịch.

## Phần cần tiếp tục trước triển khai

- Rà soát toàn bộ nhãn, dùng ảnh gốc xe máy độc lập thay cho ảnh có chữ annotate; tách bộ phát triển và bộ đánh giá.
- Cấu hình khóa JWT riêng đủ mạnh, xác minh camera/MQTT/barrier và kiểm tra thiết bị thực.
- Bổ sung kiểm thử thu hồi phiên sau thay đổi quyền/khóa tài khoản và đảm bảo việc ghi audit thất bại không bị bỏ qua. Đây chưa phải đánh giá bảo mật đầy đủ.
- Đo tải dài hạn và OCR trên điều kiện ngày/đêm/mưa/góc nghiêng trước khi chốt tiêu chí vận hành.

Không tự chấm điểm tổng thể hoặc chứng nhận production từ kết quả unit test.

## Chạy lại

```powershell
python -m pip install -r requirements_test.txt
$env:ITS_BASE_DIR = '<thu-muc-runtime-test-rieng>'
python -m pytest tests -q
python scripts/performance_smoke.py
python scripts/production_check.py
```

`requirements_test.txt` phục vụ bộ kiểm thử chính; các engine OCR thật cần dependency/model riêng. Bản `-ITS-` lồng trong dự án là bản mã nguồn cũ, không thuộc test suite chính được khai báo trong pytest.ini.
