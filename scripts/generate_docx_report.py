import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from pathlib import Path

def create_report():
    doc = docx.Document()

    # Set margins: Top 20mm, Bottom 20mm, Left 30mm, Right 20mm (Standard Vietnamese Official Margins)
    for section in doc.sections:
        section.top_margin = Inches(0.79)     # ~20mm
        section.bottom_margin = Inches(0.79)  # ~20mm
        section.left_margin = Inches(1.18)    # ~30mm
        section.right_margin = Inches(0.79)   # ~20mm

    # Colors
    NAVY = RGBColor(0, 51, 102)     # #003366 UTH Blue
    DARK_BLUE = RGBColor(0, 64, 128)
    BLACK = RGBColor(0, 0, 0)
    GRAY = RGBColor(80, 80, 80)

    # Styles
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Times New Roman'
    normal_style.font.size = Pt(13)
    normal_style.font.color.rgb = BLACK
    normal_style.paragraph_format.line_spacing = 1.25
    normal_style.paragraph_format.space_after = Pt(4)

    def set_cell_background(cell, fill_hex):
        shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
        cell._tc.get_or_add_tcPr().append(shading)

    def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
        tcPr = cell._tc.get_or_add_tcPr()
        tcMar = OxmlElement('w:tcMar')
        for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
            node = OxmlElement(f'w:{m}')
            node.set(qn('w:w'), str(val))
            node.set(qn('w:type'), 'dxa')
            tcMar.append(node)
        tcPr.append(tcMar)

    # ==================== TRANG BÌA ====================
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("BỘ GIAO THÔNG VẬN TẢI\n")
    run.font.size = Pt(13)
    run.font.bold = True
    run = p.add_run("TRƯỜNG ĐẠI HỌC GIAO THÔNG VẬN TẢI TP. HỒ CHÍ MINH (UTH)\n")
    run.font.size = Pt(14)
    run.font.bold = True
    run.font.color.rgb = NAVY
    run = p.add_run("KHOA CÔNG NGHỆ THÔNG TIN\n")
    run.font.size = Pt(13)
    run.font.bold = True
    run = p.add_run("------------------------------------")
    run.font.size = Pt(11)

    p_spacer = doc.add_paragraph()
    p_spacer.paragraph_format.space_after = Pt(36)

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p_title.add_run("BÁO CÁO HỌC PHẦN (CHƯƠNG 1 & CHƯƠNG 2)\n")
    run.font.size = Pt(15)
    run.font.bold = True
    run.font.color.rgb = DARK_BLUE
    run = p_title.add_run("ĐẶC TẢ YÊU CẦU PHẦN MỀM SƠ BỘ (SRS) & BẢNG PHÂN RÃ CÔNG VIỆC (WBS)\n\n")
    run.font.size = Pt(16)
    run.font.bold = True
    run.font.color.rgb = NAVY

    run = p_title.add_run("Đề tài:\n")
    run.font.size = Pt(13)
    run.font.italic = True
    run = p_title.add_run("XÂY DỰNG HỆ THỐNG QUẢN LÝ BÃI ĐỖ XE THÔNG MINH ĐA KHU VỰC TẠI TRƯỜNG ĐẠI HỌC GIAO THÔNG VẬN TẢI TP.HCM CƠ SỞ 1 ỨNG DỤNG AI VÀ THẺ RFID\n")
    run.font.size = Pt(15)
    run.font.bold = True
    run.font.color.rgb = NAVY

    p_spacer2 = doc.add_paragraph()
    p_spacer2.paragraph_format.space_after = Pt(28)

    p_info = doc.add_paragraph()
    p_info.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_info.paragraph_format.left_indent = Inches(0.8)
    
    r = p_info.add_run("Học phần:\t\t")
    r.font.bold = True
    p_info.add_run("Đồ án thực tế Công nghệ phần mềm (Capstone Project on SE)\n")
    
    r = p_info.add_run("Mã học phần:\t")
    r.font.bold = True
    p_info.add_run("122039  |  ")
    r = p_info.add_run("Mã lớp học phần: ")
    r.font.bold = True
    p_info.add_run("012012213907\n")

    r = p_info.add_run("Giảng viên hướng dẫn:\t")
    r.font.bold = True
    r2 = p_info.add_run("Thầy Vũ Đình Long\n")
    r2.font.bold = True
    r2.font.color.rgb = NAVY

    r = p_info.add_run("Nhóm thực hiện:\t")
    r.font.bold = True
    p_info.add_run("Nhóm Đặng Đình Khang (STT 46 - 49)\n")

    r = p_info.add_run("Thành viên nhóm:\n")
    r.font.bold = True
    p_info.add_run("   1. Đặng Đình Khang\t\tMSSV: 027206013096 (Nhóm trưởng)\n")
    p_info.add_run("   2. Nguyễn Quang Huy\t\tMSSV: 034206012355 (Tech Lead)\n")
    p_info.add_run("   3. Nguyễn Xuân Hoàng\tMSSV: 66206000135\n")
    p_info.add_run("   4. Thạch Thị Trâm\t\tMSSV: 51306002444\n")

    p_spacer3 = doc.add_paragraph()
    p_spacer3.paragraph_format.space_after = Pt(40)

    p_foot = doc.add_paragraph()
    p_foot.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p_foot.add_run("TP. HỒ CHÍ MINH, THÁNG 10 NĂM 2026")
    r.font.bold = True

    doc.add_page_break()

    # ==================== PHẦN 1 ====================
    h1 = doc.add_heading(level=1)
    r = h1.add_run("PHẦN I: TỔNG QUAN HỌC PHẦN, QUY TRÌNH & ĐÁNH GIÁ ĐỒ ÁN")
    r.font.color.rgb = NAVY

    doc.add_heading("1.1. Thông tin học phần & Chuẩn đầu ra (CLOs)", level=2)
    p = doc.add_paragraph()
    p.add_run("Học phần ").font.size = Pt(13)
    r = p.add_run("Đồ án thực tế Công nghệ phần mềm (Mã HP: 122039)")
    r.font.bold = True
    p.add_run(" là học phần bắt buộc thuộc khối kiến thức chuyên ngành Công nghệ thông tin tại Trường Đại học Giao thông Vận tải TP.HCM (UTH), có khối lượng 3 tín chỉ (90 tiết dự án và 90 tiết tự học). Học phần trang bị kỹ năng phân tích, thiết kế, hiện thực hóa và kiểm thử phần mềm thực tế.\n\nTheo đề cương chi tiết học phần, sinh viên cần đạt 3 chuẩn đầu ra cốt lõi:")
    
    p = doc.add_paragraph(style='List Bullet')
    r = p.add_run("CLO1: ")
    r.font.bold = True
    p.add_run("Sử dụng công nghệ tiên tiến để lựa chọn giải pháp tối ưu cho từng bài toán xây dựng phần mềm cụ thể; điều hành hoạt động toàn bộ một dự án phần mềm; áp dụng kiến thức thực hiện các nhiệm vụ cụ thể trong bài toán thực tế.")

    p = doc.add_paragraph(style='List Bullet')
    r = p.add_run("CLO2: ")
    r.font.bold = True
    p.add_run("Lập kế hoạch xây dựng dự án khởi nghiệp dựa trên sản phẩm dự án; đánh giá tính khả thi và tiềm năng ứng dụng thực tế.")

    p = doc.add_paragraph(style='List Bullet')
    r = p.add_run("CLO3: ")
    r.font.bold = True
    p.add_run("Xây dựng quy trình hoạt động nhóm hiệu quả, chuyên nghiệp, đáp ứng tình huống cụ thể; xây dựng nội dung thuyết trình và bảo vệ quan điểm khoa học.")

    doc.add_heading("1.2. Quy trình thực hiện qua 5 giai đoạn học phần", level=2)
    p = doc.add_paragraph()
    p.add_run("Quá trình thực hiện đồ án được tổ chức chặt chẽ theo 5 chương tương ứng với vòng đời phát triển phần mềm:")
    p = doc.add_paragraph(style='List Bullet')
    p.add_run("Chương 1: Giới thiệu chung, phân chia nhóm, lựa chọn đề tài và ôn tập kiến thức thiết kế phần mềm.")
    p = doc.add_paragraph(style='List Bullet')
    p.add_run("Chương 2: Khảo sát thực tế bài toán, phân tích yêu cầu, lập kế hoạch WBS và nộp bản SRS sơ bộ (Giai đoạn hiện tại).")
    p = doc.add_paragraph(style='List Bullet')
    p.add_run("Chương 3: Báo cáo đồ án giữa kỳ, thuyết trình tiến độ và hiệu chỉnh kế hoạch phát triển.")
    p = doc.add_paragraph(style='List Bullet')
    p.add_run("Chương 4: Hoàn thiện phần mềm, kiểm soát dự án và tích hợp hệ thống.")
    p = doc.add_paragraph(style='List Bullet')
    p.add_run("Chương 5: Báo cáo đồ án cuối kỳ, thuyết trình sản phẩm thực tế và nghiệm thu toàn diện.")

    doc.add_heading("1.3. Cơ cấu đánh giá & Các Rubrics chấm điểm", level=2)
    p = doc.add_paragraph()
    p.add_run("Điểm số học phần được đánh giá toàn diện gồm 2 thành phần chính:\n")
    p.add_run("• Đánh giá quá trình (Trọng số 20%): Thuyết trình, báo cáo nhóm định kỳ, biên bản họp nhóm và tiến độ công việc.\n• Đánh giá cuối kỳ (Trọng số 80%): Báo cáo đồ án hoàn chỉnh và thuyết trình bảo vệ sản phẩm chạy thực tế.")
    
    p = doc.add_paragraph()
    p.add_run("Nhóm cam kết tuân thủ nghiêm ngặt các bảng Rubric đánh giá trong phụ lục đề cương:")
    p = doc.add_paragraph(style='List Bullet')
    r = p.add_run("Rubric A6.1 (Đánh giá cá nhân trong làm việc nhóm): ")
    r.font.bold = True
    p.add_run("Thời gian tham gia họp đầy đủ (15%), thái độ kết nối tốt (15%), đóng góp ý kiến sáng tạo hữu ích (20%), giao nộp sản phẩm đúng hạn (20%), chất lượng sản phẩm đáp ứng tốt (30%).")
    p = doc.add_paragraph(style='List Bullet')
    r = p.add_run("Rubric A5.4 (Đánh giá bài nộp báo cáo): ")
    r.font.bold = True
    p.add_run("Thể thức văn bản nhất quán, không lỗi chính tả (10%), cấu trúc cân đối hợp lý (10%), lập luận hoàn toàn chặt chẽ logic (20%), nội dung đáp ứng đầy đủ yêu cầu (40%), kết luận phù hợp (20%).")
    p = doc.add_paragraph(style='List Bullet')
    r = p.add_run("Rubric A5.5 (Đánh giá thuyết trình): ")
    r.font.bold = True
    p.add_run("Nội dung phong phú chính xác khoa học (30%), cấu trúc slide trực quan thẩm mỹ (20%), kỹ năng trình bày tương tác tốt (30%), trả lời câu hỏi thỏa đáng và phối hợp nhóm tốt (20%).")

    doc.add_heading("1.4. Ôn tập bốn trụ cột Thiết kế Phần mềm (Software Design Review)", level=2)
    p = doc.add_paragraph()
    p.add_run("Dưới sự hướng dẫn của Thầy Vũ Đình Long trong Chương 1, nhóm đã hệ thống hóa và ôn tập 4 trụ cột thiết kế phần mềm cốt lõi để áp dụng trực tiếp vào dự án:")
    
    p = doc.add_paragraph()
    r = p.add_run("1. Thiết kế Dữ liệu (Data Design): ")
    r.font.bold = True
    p.add_run("Mô hình hóa thực thể liên kết (ERD), áp dụng chuẩn hóa bậc 3 (3NF) để loại bỏ trùng lặp và dị thường cập nhật, thiết lập toàn vẹn tham chiếu chặt chẽ giữa thẻ RFID, lượt xe vào ra, ca trực và nhật ký kiểm toán.")

    p = doc.add_paragraph()
    r = p.add_run("2. Thiết kế Kiến trúc (Architectural Design): ")
    r.font.bold = True
    p.add_run("Áp dụng mô hình kiến trúc phân tầng mô-đun hóa (Layered Modular Architecture) gồm Presentation Layer (Web SPA), API Layer (FastAPI RESTful), Service Layer (Domain Logic) và Persistence Layer (Database Repository).")

    p = doc.add_paragraph()
    r = p.add_run("3. Thiết kế Giao diện (Interface / UI-UX Design): ")
    r.font.bold = True
    p.add_run("Tối ưu hóa thao tác người dùng (Human-in-the-loop) cho nhân viên bảo vệ: giao diện trạm POS phân làn rõ ràng, hỗ trợ phím tắt Space/Enter thao tác nhanh dưới 1.5 giây, hiển thị mã VietQR to rõ và trực quan hóa sức chứa 4 khu UTH.")

    p = doc.add_paragraph()
    r = p.add_run("4. Thiết kế Thành phần & Mẫu thiết kế (Component Design & Design Patterns): ")
    r.font.bold = True
    p.add_run("Tuân thủ các nguyên lý SOLID, áp dụng Strategy Pattern cho bộ tính phí (5k trong ngày / 10k qua đêm), Adapter Pattern cho kết nối camera và đầu đọc thẻ, Repository Pattern cho truy xuất CSDL.")

    # ==================== PHẦN 2 ====================
    doc.add_page_break()
    h1 = doc.add_heading(level=1)
    r = h1.add_run("PHẦN II: BIÊN BẢN LÀM VIỆC NHÓM & BẢNG PHÂN RÃ CÔNG VIỆC (WBS)")
    r.font.color.rgb = NAVY

    doc.add_heading("2.1. Danh sách thành viên và phân công chuyên trách", level=2)
    p = doc.add_paragraph()
    p.add_run("Dựa trên năng lực chuyên môn và thảo luận nội bộ, nhóm thống nhất cơ cấu phân công nhiệm vụ chi tiết nhằm đảm bảo tối đa hóa hiệu quả theo Rubric A6.1:")

    table = doc.add_table(rows=1, cols=4)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = table.rows[0].cells
    hdr[0].text = "Họ và tên / MSSV"
    hdr[1].text = "Vai trò"
    hdr[2].text = "Trọng tâm đảm nhiệm"
    hdr[3].text = "Khối lượng bàn giao (Deliverables)"
    for cell in hdr:
        set_cell_background(cell, "003366")
        set_cell_margins(cell, 120, 120, 150, 150)
        for p in cell.paragraphs:
            p.runs[0].font.color.rgb = RGBColor(255, 255, 255)
            p.runs[0].font.bold = True

    members = [
        ("Nguyễn Quang Huy\n034206012355", "Tech Lead / Core Backend", "Gánh toàn bộ phần khó nhất: Backend Architecture, API Gateway đa cổng, Pipeline AI Vision ALPR nhận diện biển số, Cổng thanh toán VietQR động 5k/10k, Bảo mật PBKDF2/JWT/RBAC và Audit Logs.", "Bộ mã nguồn Backend API FastAPI hoàn chỉnh, Pipeline AI ALPR độ chính xác cao, Module VietQR động, Hệ thống bảo mật & Audit log."),
        ("Đặng Đình Khang\n027206013096", "Nhóm trưởng / Frontend & Thuật toán", "Toàn bộ Giao diện Web Frontend (SPA) Trạm POS bảo vệ đa cổng, Thuật toán Điều phối Làn xe linh hoạt (Reversible Lane), Thuật toán Tính toán Sức chứa thời gian thực 4 Khu (A, B, C, E), và Tích hợp UI với API.", "Toàn bộ mã nguồn Web UI (frontend/web/), Thuật toán điều phối làn và sức chứa, Giao diện POS bảo vệ trực quan."),
        ("Nguyễn Xuân Hoàng\n66206000135", "Nghiệp vụ, Kiểm thử & Báo cáo Excel", "Module Quản lý Ca trực (Shift Management) & Đối soát tiền vé theo từng cổng, Module Xử lý Sự cố mất thẻ xe (Lost Card Workflow), Viết bộ Kiểm thử tự động (Pytest), và Script xuất báo cáo Excel (.xlsx).", "Module quản lý ca trực & đối soát tiền, Module xử lý sự cố mất thẻ, Bộ test tự động pytest (>40 test cases), Script xuất báo cáo Excel (openpyxl)."),
        ("Thạch Thị Trâm\n51306002444", "Báo cáo chính, CSDL & Thuyết trình", "Chịu trách nhiệm Báo cáo chính: Biên soạn tài liệu SRS sơ bộ và Báo cáo đồ án hoàn chỉnh chuẩn IEEE; Thiết kế Cơ sở dữ liệu (CSDL) & Vẽ sơ đồ ERD 3NF; Thiết kế Bộ Slide thuyết trình (Canva/PPT) chuyên nghiệp.", "File tài liệu SRS và Báo cáo đồ án (.docx/PDF), Sơ đồ CSDL ERD 3NF chuẩn mực, Bộ Slide thuyết trình đồ án chuyên nghiệp, Biên bản họp nhóm định kỳ.")
    ]

    for m in members:
        row = table.add_row().cells
        for i, val in enumerate(m):
            row[i].text = val
            set_cell_margins(row[i], 100, 100, 120, 120)

    doc.add_heading("2.2. Kế hoạch tiến độ 4 Sprint (Mô hình Agile/Scrum)", level=2)
    p = doc.add_paragraph()
    p.add_run("Nhóm áp dụng mô hình phát triển Agile/Scrum với 4 Sprint (mỗi Sprint 2 tuần):")
    p = doc.add_paragraph(style='List Bullet')
    p.add_run("Sprint 1 (Tuần 1 - 2): Khởi động dự án, khảo sát thực địa UTH CS1, đặc tả SRS sơ bộ, lập bảng WBS, thiết lập workspace Git.")
    p = doc.add_paragraph(style='List Bullet')
    p.add_run("Sprint 2 (Tuần 3 - 4): Thiết kế kiến trúc phân tầng, thiết kế CSDL ERD 3NF đa trạm, vẽ bộ sơ đồ UML (Use Case, Sequence, Class).")
    p = doc.add_paragraph(style='List Bullet')
    p.add_run("Sprint 3 (Tuần 5 - 6): Hiện thực hóa Core Backend API, tối ưu Pipeline AI Camera sau, xây dựng giao diện Web POS và tích hợp VietQR động.")
    p = doc.add_paragraph(style='List Bullet')
    p.add_run("Sprint 4 (Tuần 7 - 8): Kiểm thử tự động (Pytest), kiểm thử tải, đối soát tài chính ca trực, đóng gói sản phẩm và báo cáo tổng kết.")

    doc.add_heading("2.3. Bảng Phân rã Công việc chi tiết (WBS Matrix)", level=2)
    p = doc.add_paragraph()
    p.add_run("Bảng phân rã công việc (WBS) chi tiết từ WBS 1.0 đến WBS 5.0, gán rõ người phụ trách chính và sản phẩm bàn giao:")

    wbs_table = doc.add_table(rows=1, cols=4)
    wbs_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    w_hdr = wbs_table.rows[0].cells
    w_hdr[0].text = "Mã WBS"
    w_hdr[1].text = "Hạng mục công việc (Task Description)"
    w_hdr[2].text = "Phụ trách chính"
    w_hdr[3].text = "Sản phẩm bàn giao (Deliverable)"
    for cell in w_hdr:
        set_cell_background(cell, "003366")
        set_cell_margins(cell, 100, 100, 120, 120)
        for p in cell.paragraphs:
            p.runs[0].font.color.rgb = RGBColor(255, 255, 255)
            p.runs[0].font.bold = True

    wbs_items = [
        ("WBS 1.1", "Viết tài liệu Đặc tả SRS sơ bộ chuẩn IEEE 830 bám sát bãi xe UTH CS1", "Thạch Thị Trâm", "File docs/SRS_SO_BO_SMART_PARKING_UTH_SE.md"),
        ("WBS 1.2", "Xây dựng Bảng phân rã công việc WBS & Kế hoạch tiến độ 4 Sprint", "Đặng Đình Khang", "Biên bản & Bảng WBS Sprint 1"),
        ("WBS 1.3", "Khởi tạo Git Workspace, cấu hình .gitignore, phân quyền cộng tác", "Nguyễn Quang Huy", "Git Repository chuẩn mực (nhánh main/develop)"),
        ("WBS 2.1", "Thiết kế Sơ đồ Use Case tổng thể & chi tiết các trạm Cổng 1, 2, 3", "Đặng Đình Khang", "Diagram Use Case chi tiết"),
        ("WBS 2.2", "Thiết kế Cơ sở dữ liệu (CSDL) & Vẽ sơ đồ ERD chuẩn 3NF", "Thạch Thị Trâm", "Sơ đồ ERD & Script Schema DB"),
        ("WBS 2.3", "Thiết kế Sơ đồ tuần tự (Sequence Diagram) luồng vào Cổng 1 - ra Cổng 2/3", "Nguyễn Quang Huy", "Sơ đồ Sequence Diagram"),
        ("WBS 2.4", "Thiết kế Wireframe/UI Mockup cho Trạm POS đa làn & Dashboard 4 khu", "Đặng Đình Khang", "Bản thiết kế giao diện Figma/Mockup"),
        ("WBS 3.1", "Tái cấu trúc Backend Service theo mô hình phân tầng chuẩn mực", "Nguyễn Quang Huy", "Module backend/ phân tầng sạch sẽ"),
        ("WBS 3.2", "Hiện thực hóa Core API Xe vào Cổng 1 & Xe ra Trạm B/C/AE (Khớp biển)", "Nguyễn Quang Huy", "backend/parking_service.py & API routes"),
        ("WBS 3.3", "Phát triển module Tính phí đồng giá 5k & Phụ phí qua đêm 5k (Tổng 10k)", "Nguyễn Quang Huy", "Module tính tiền tariff engine"),
        ("WBS 3.4", "Tích hợp dịch vụ Sinh mã VietQR 5k/10k động chuẩn Napas 247", "Nguyễn Quang Huy", "Module VietQR Payment"),
        ("WBS 3.5", "Tối ưu Pipeline AI Vision ALPR nhận diện biển số xe máy từ Camera sau", "Nguyễn Quang Huy", "backend/alpr_service.py tối ưu camera sau"),
        ("WBS 3.6", "Xây dựng Thuật toán Điều phối Làn linh hoạt & Đếm sức chứa 4 khu", "Đặng Đình Khang", "Thuật toán điều phối làn & sức chứa"),
        ("WBS 3.7", "Xây dựng toàn bộ Giao diện POS Trạm bảo vệ: Chọn cổng/làn, quét thẻ", "Đặng Đình Khang", "frontend/web/app.js & index.html"),
        ("WBS 3.8", "Thiết kế Modal Popup hiển thị Mã VietQR 5k/10k tự động khi xe ra", "Đặng Đình Khang", "Giao diện thanh toán QR"),
        ("WBS 3.9", "Xây dựng Dashboard Sơ đồ 4 khu hiển thị tỷ lệ lấp đầy bãi xe UTH", "Đặng Đình Khang", "Giao diện Dashboard Sức chứa"),
        ("WBS 3.10", "Xây dựng module Quản lý Ca trực bảo vệ & Báo cáo đối soát theo cổng", "Nguyễn Xuân Hoàng", "API & Màn hình chốt ca đối soát tiền"),
        ("WBS 3.11", "Xây dựng quy trình Xử lý sự cố mất thẻ xe (truy vết ảnh camera sau)", "Nguyễn Xuân Hoàng", "Module xử lý mất thẻ xe"),
        ("WBS 4.1", "Lập Kế hoạch kiểm thử (Test Plan) & Ma trận trường hợp kiểm thử", "Thạch Thị Trâm", "File docs/TEST_PLAN.md"),
        ("WBS 4.2", "Viết Unit Test và Integration Test tự động bằng pytest (>40 test cases)", "Nguyễn Xuân Hoàng", "Thư mục tests/ tự động hóa"),
        ("WBS 4.3", "Đánh giá Benchmark độ chính xác ALPR trên tập dữ liệu xe máy UTH", "Nguyễn Xuân Hoàng", "Báo cáo Benchmark Accuracy"),
        ("WBS 4.4", "Kiểm thử bảo mật (Phân quyền RBAC, Hash PBKDF2, Lockout brute-force)", "Nguyễn Quang Huy", "Báo cáo Security Audit"),
        ("WBS 5.1", "Đóng gói hệ thống chạy 1-click (Script start.bat / Docker Compose)", "Nguyễn Xuân Hoàng", "File đóng gói ứng dụng"),
        ("WBS 5.2", "Biên soạn toàn bộ Báo cáo đồ án hoàn chỉnh (Final Report chuẩn IEEE)", "Thạch Thị Trâm", "Báo cáo đồ án cuối kỳ hoàn chỉnh"),
        ("WBS 5.3", "Thiết kế Bộ Slide thuyết trình (Canva/PPT) chuyên nghiệp & Kịch bản", "Thạch Thị Trâm", "Slide thuyết trình & Video demo")
    ]

    for item in wbs_items:
        row = wbs_table.add_row().cells
        for i, val in enumerate(item):
            row[i].text = val
            set_cell_margins(row[i], 80, 80, 100, 100)

    doc.add_heading("2.4. Review Workspace Git & Quy ước quản trị mã nguồn", level=2)
    p = doc.add_paragraph()
    p.add_run("Nhóm đã thiết lập Git repository chính thức trên máy và tuân thủ các quy ước chuẩn công nghiệp:\n")
    p.add_run("• Phân nhánh Git: Nhánh main (ổn định nộp bài), develop (nhánh tích hợp chính của nhóm), feature/* (nhánh phát triển tính năng riêng của từng thành viên).\n• Quy ước Commit (Conventional Commits): feat (tính năng mới), fix (sửa lỗi), docs (tài liệu), refactor (tái cấu trúc code), test (kiểm thử tự động).")

    # ==================== PHẦN 3 ====================
    doc.add_page_break()
    h1 = doc.add_heading(level=1)
    r = h1.add_run("PHẦN III: ĐẶC TẢ YÊU CẦU PHẦN MỀM SƠ BỘ (PRELIMINARY SRS)")
    r.font.color.rgb = NAVY

    doc.add_heading("3.1. Khảo sát thực địa bãi xe UTH Cơ sở 1 (Số 2 Võ Oanh)", level=2)
    p = doc.add_paragraph()
    p.add_run("Hệ thống được thiết kế 'may đo' bám sát chính xác 100% hiện trạng mặt bằng tại UTH Cơ sở 1:")
    p = doc.add_paragraph(style='List Bullet')
    p.add_run("4 Khu vực đỗ xe trong trường theo thứ tự quy hoạch A - E - C - B: Gồm Khu A (Sân ngoài trời), Khu E (Nhà xe kết cấu thép 4 tầng: các tầng dưới cho CB-GV-CNV, chỉ duy nhất lầu trên cùng cho sinh viên), Khu C (Sân ngoài trời), và Khu B (Sân ngoài trời).")
    p = doc.add_paragraph(style='List Bullet')
    p.add_run("Cổng 1 (Võ Oanh - Cổng vào tập trung): Gồm 4 làn vào song song, có chức năng quẹt thẻ RFID và chỉ định khu đỗ để theo dõi chính xác sức chứa.")
    p = doc.add_paragraph(style='List Bullet')
    p.add_run("Cổng 2 (Cổng xả Khu C & B): Gồm Trạm ra Khu C (1 trạm gồm 2 làn quẹt thẻ) và Trạm ra Khu B (4 làn quẹt thẻ) cùng đổ ra Cổng 2.")
    p = doc.add_paragraph(style='List Bullet')
    p.add_run("Cổng 3 (Cổng xả Khu A & E): Gồm Trạm ra Khu A & E (2 làn quẹt thẻ ra).")
    p = doc.add_paragraph(style='List Bullet')
    p.add_run("Thiết bị kiểm soát: Máy tính để bàn + 1 Camera chụp sau đuôi xe máy (Rear Camera ALPR) + Đầu đọc thẻ RFID quẹt tay.")
    p = doc.add_paragraph(style='List Bullet')
    p.add_run("Định danh bảo mật: Sử dụng thẻ trắng chỉ in Logo UTH (không in số thứ tự hay biển số bằng mắt thường), bảo mật tuyệt đối qua chip RFID.")

    doc.add_heading("3.2. Yêu cầu chức năng cốt lõi (Functional Requirements - FR)", level=2)
    p = doc.add_paragraph(style='List Bullet')
    p.add_run("FR 1 (Quản lý Xe vào tại Cổng 1): Tiếp nhận quẹt thẻ RFID trên 4 làn vào; phân biệt đối tượng Cán bộ - Giảng viên (miễn phí 0đ, tầng dưới Khu E) và Sinh viên (5.000đ, chỉ lầu trên cùng Khu E); Camera sau tự động chụp biển số; nhận diện ALPR; gán khu đỗ (A, E, C, B) và giảm 1 chỗ trống tương ứng; tạo vé trạng thái IN_PARKING.")
    p = doc.add_paragraph(style='List Bullet')
    p.add_run("FR 2 (Quản lý Xe ra & Đối chiếu chéo): Quẹt thẻ tại Trạm C (2 làn), Trạm B (4 làn) (Cổng 2) hoặc Trạm A-E (Cổng 3); Camera sau chụp biển xe ra; tự động đối chiếu với biển xe vào. Nếu MATCH -> cán bộ tự động mở barrier miễn phí 0đ, sinh viên thu phí 5k/10k; nếu MISMATCH -> bật cảnh báo đỏ khóa cổng.")
    p = doc.add_paragraph(style='List Bullet')
    p.add_run("FR 3 (Thu phí & Miễn phí Cán bộ): Cán bộ - Giảng viên - CNV (CB-GV-CNV) hoàn toàn miễn phí 0 VNĐ, barrier tự động mở khi quẹt thẻ; Sinh viên thu phí đồng giá 5.000 VNĐ / lượt trong ngày; tự động tính phụ phí qua đêm thêm 5.000 VNĐ (tổng 10.000 VNĐ) nếu gửi qua 23h00 đêm; hỗ trợ tiền mặt và quét mã VietQR động chuẩn Napas 247.")
    p = doc.add_paragraph(style='List Bullet')
    p.add_run("FR 4 (Giám sát Sức chứa 4 Khu): Đếm chính xác số xe đang đỗ và số chỗ còn trống theo thời gian thực theo thứ tự A - E - C - B (Sân A, Nhà xe Khu E nhiều tầng, Sân C, Sân B); hiển thị cảnh báo đỏ khi khu đỗ đạt ngưỡng đầy.")
    p = doc.add_paragraph(style='List Bullet')
    p.add_run("FR 5 (Quản lý Ca trực & Đối soát): Bảo vệ mở ca, chốt ca độc lập theo từng trạm; hệ thống tự động bóc tách doanh thu tiền mặt nộp quỹ và tiền chuyển khoản VietQR.")
    p = doc.add_paragraph(style='List Bullet')
    p.add_run("FR 6 (Xử lý Mất thẻ & Audit Log): Quy trình xử lý mất thẻ cho phép truy vết ảnh camera sau lúc vào, khóa vĩnh viễn thẻ LOST; lưu nhật ký kiểm toán không thể xóa sửa.")

    doc.add_heading("3.3. Yêu cầu phi chức năng (Non-Functional Requirements - NFR)", level=2)
    p = doc.add_paragraph(style='List Bullet')
    p.add_run("NFR 1 (Hiệu năng): Thời gian phản hồi từ lúc quẹt thẻ đến khi nhận diện và hiển thị kết quả <= 1.5 giây / lượt xe, đảm bảo không ùn tắc cổng vào giờ cao điểm.")
    p = doc.add_paragraph(style='List Bullet')
    p.add_run("NFR 2 (Độ chính xác ALPR): Độ chính xác nhận diện biển số xe máy đạt >= 95% trong điều kiện bình thường và >= 90% trong điều kiện thiếu sáng nhà lầu E.")
    p = doc.add_paragraph(style='List Bullet')
    p.add_run("NFR 3 (Bảo mật): Mật khẩu mã hóa PBKDF2 với Salt ngẫu nhiên, xác thực API bằng signed JWT token, tự động lockout sau 5 lần đăng nhập sai.")
    p = doc.add_paragraph(style='List Bullet')
    p.add_run("NFR 4 (Kiểm thử): Bộ kiểm thử tự động pytest bao phủ >= 80% các luồng nghiệp vụ.")

    doc.add_heading("3.4. Ràng buộc pháp lý & Quy chuẩn kỹ thuật (Regulatory Constraints)", level=2)
    p = doc.add_paragraph(style='List Bullet')
    p.add_run("Khung giá vé: Tuân thủ Quyết định số 35/2018/QĐ-UBND của UBND TP.HCM về giá dịch vụ trông giữ xe tại các trường học trên địa bàn Thành phố.")
    p = doc.add_paragraph(style='List Bullet')
    p.add_run("Giá trị pháp lý vé xe: Đáp ứng Điều 554 - 557 Bộ luật Dân sự 2015 thông qua việc lưu trữ ảnh chụp đuôi xe, thời gian và dữ liệu vé số hóa làm bằng chứng gửi giữ tài sản.")
    p = doc.add_paragraph(style='List Bullet')
    p.add_run("An toàn PCCC: Đáp ứng QCVN 06:2022/BXD thông qua module giám sát sức chứa không để xe vượt quá công suất gây cản trở thoát nạn.")
    p = doc.add_paragraph(style='List Bullet')
    p.add_run("Chuyển đổi số: Hưởng ứng Quyết định 1813/QĐ-TTg của Thủ tướng Chính phủ về thanh toán không tiền mặt trong cơ sở giáo dục thông qua mã VietQR.")

    # ==================== PHẦN 4 ====================
    doc.add_page_break()
    h1 = doc.add_heading(level=1)
    r = h1.add_run("PHẦN IV: CÁC CÂU HỎI TRAO ĐỔI VỚI GIẢNG VIÊN VŨ ĐÌNH LONG")
    r.font.color.rgb = NAVY

    p = doc.add_paragraph()
    p.add_run("Trong buổi review tuần tới, nhóm dự kiến xin ý kiến chỉ đạo chuyên môn của Thầy Vũ Đình Long về 3 nội dung trọng tâm sau:")

    p = doc.add_paragraph()
    r = p.add_run("Câu hỏi 1: ")
    r.font.bold = True
    p.add_run("Thưa Thầy, từ đề tài ITS cũ, nhóm em đã mở rộng bài toán bám sát chính xác mặt bằng thực tế của UTH Cơ sở 1 gồm 4 khu (A, B, C, E) và 3 cổng (8 làn xe) với cơ chế đồng bộ đa trạm và đối chiếu chéo. Thầy nhận xét về hướng tiếp cận mở rộng theo cấu trúc thực tế này của nhóm đã đáp ứng đúng kỳ vọng của đồ án Capstone SE chưa ạ?")

    p = doc.add_paragraph()
    r = p.add_run("Câu hỏi 2: ")
    r.font.bold = True
    p.add_run("Thưa Thầy, theo đề cương chi tiết học phần môn Đồ án thực tế CNPM (Mã HP: 122039), nhóm tập trung tối đa nguồn lực vào phần mềm, kiến trúc phân tầng, CSDL quan hệ 3NF và kiểm thử tự động pytest; toàn bộ phần cứng (camera, thẻ từ) được nhóm trừu tượng hóa qua Adapter Pattern (dùng WebRTC Camera và Virtual RFID Card để kiểm thử). Thầy có yêu cầu nhóm phải kết nối phần cứng công nghiệp ngoại vi nào thêm không ạ?")

    p = doc.add_paragraph()
    r = p.add_run("Câu hỏi 3: ")
    r.font.bold = True
    p.add_run("Thưa Thầy, đối với nghiệp vụ phụ phí gửi xe qua đêm (5k vé lượt ban ngày + 5k phụ phí qua đêm = 10k), nhóm thiết lập mốc chuyển ca đêm tự động là 23h00 thì đã phù hợp với nội quy thực tế của khuôn viên trường chưa ạ?")

    p_spacer = doc.add_paragraph()
    p_spacer.paragraph_format.space_after = Pt(20)

    # Chữ ký nhóm trưởng
    p_sign = doc.add_paragraph()
    p_sign.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_sign.paragraph_format.right_indent = Inches(0.5)
    p_sign.add_run("TP. Hồ Chí Minh, ngày 19 tháng 10 năm 2026\n").font.italic = True
    r = p_sign.add_run("ĐẠI DIỆN NHÓM SINH VIÊN (NHÓM TRƯỞNG)\n\n\n\n")
    r.font.bold = True
    r2 = p_sign.add_run("ĐẶNG ĐÌNH KHANG")
    r2.font.bold = True

    # Save
    out_path = Path("docs/BAO_CAO_SRS_SO_BO_VA_WBS_NHOM_DANG_DINH_KHANG.docx")
    doc.save(out_path)
    print(f"Report generated successfully: {out_path}")

if __name__ == "__main__":
    create_report()
