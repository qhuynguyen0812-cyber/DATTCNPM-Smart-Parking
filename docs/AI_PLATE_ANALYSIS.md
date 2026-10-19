# AI phân tích biển số — tích hợp ngày 06/09/2026

Đã sửa trực tiếp trong dự án. Chưa xác minh suy luận AI thật vì máy chưa chạy 9Router và chưa có API key.

## Chức năng đã gắn

- Vision đọc ảnh gốc trước EasyOCR. Giữ model `cx/gpt-5.5` theo cấu hình 9Router của dự án.
- Trả biển số, loại xe, bố cục một/hai dòng, số biển nhìn thấy, cảnh báo mờ/chói/che khuất và ký tự chưa rõ.
- Không tự gán confidence 80%; Vision trả `confidence=null`.
- Không tự lấp ký tự `?`, không chọn tùy tiện khi ảnh có nhiều biển, không thay kết quả AI từ chối đọc bằng dự đoán khác mà không báo.
- Giao diện xe vào/ra có phần giải thích AI, nút phân tích lại và ô xác nhận đã đối chiếu ảnh.
- Vé lưu yêu cầu kiểm tra OCR; xe ra chưa được xác nhận vẫn vào hàng chờ kiểm tra dù chuỗi biển khớp.
- Khi AI chưa sẵn sàng, OCR cục bộ là dự phòng và được ghi rõ trạng thái.
- Có cấu hình giao thức Responses hoặc Chat Completions, timeout 45 giây mỗi request và tối đa một lần retry SDK.
- Ảnh kiểm tra định dạng/nội dung, tối đa 12 MB và 20 megapixel, được xoay theo EXIF rồi mã hóa JPEG tối đa 1920 px, không giữ EXIF.

## Kết quả kiểm thử

- 220/220 test đạt, 34 cảnh báo, 17,23 giây.
- 7 màn hình Streamlit không có exception.
- Thử thao tác trên thẻ AI và ô xác nhận đối chiếu ở màn hình xe vào: đạt.
- SDK thật gửi/nhận đúng JSON Schema với HTTP server kiểm thử cục bộ: đạt. Server này trả dữ liệu giả lập có kiểm soát, không phải model AI.
- Chưa có kết quả nhận diện ảnh từ 9Router/AI thật; không khẳng định độ chính xác đã tăng.

## Bật AI thật

1. Khởi động dịch vụ 9Router của bạn và bảo đảm model `cx/gpt-5.5` hỗ trợ ảnh/JSON Schema.
2. Tại thư mục dự án, chạy công cụ cấu hình. Khóa được nhập ẩn và chỉ lưu trong `.env` ở máy chạy ứng dụng:

```powershell
& 'C:\Users\ADMIN\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' scripts/configure_ai.py
```

Giữ Base URL `http://localhost:20128/v1` nếu đúng cổng router của bạn. Công cụ cho phép nhập URL/model khác. Chọn `responses` hoặc `chat` theo API router thực sự hỗ trợ.

3. Khởi động lại Streamlit/API, tải ảnh và xem phần “AI phân tích biển số”. `--check` chỉ kiểm tra cấu hình, không xác nhận model hoạt động.

Không gửi API key vào cuộc trò chuyện. Không commit `.env`. File này đã nằm trong quy tắc ignore của dự án.

## API

- `GET /ai/status`: cần bearer token; không trả khóa API.
- `POST /ocr`: tự ưu tiên Vision khi bật; phản hồi có `ai_analysis`, `ai_status`, `review_required`.
- `POST /vehicle/entry`, `/vehicle/exit`: thêm form `ai_review_confirmed=true` khi người vận hành đã đối chiếu ảnh.
- Việc xác nhận không cho phép bỏ qua quy trình xử lý biển xe ra không khớp.

## Tài liệu đối chiếu

Cấu trúc gửi ảnh và JSON Schema được đối chiếu với [Images and vision](https://developers.openai.com/api/docs/guides/images-vision) và [Structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs). Tính tương thích của 9Router cần được kiểm tra với dịch vụ thật.
