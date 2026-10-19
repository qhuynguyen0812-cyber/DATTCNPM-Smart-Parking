import re
from datetime import datetime
from pathlib import Path

import streamlit as st

from backend.app_service import confirm_vehicle_entry, confirm_vehicle_exit, process_plate_image
from backend.config import APP_TITLE
from backend.db import fetch_logs, get_active_tickets, init_db
from backend.storage import save_uploaded_file
from backend.validators import ValidationError
from frontend.analytics import render_analytics_dashboard
from frontend.ui import (
    render_capture_details,
    render_custom_css,
    render_dashboard_metrics,
    render_dashboard_shell_end,
    render_dashboard_shell_start,
    render_logs_table,
    render_ocr_result,
    render_panel_header,
    render_section_wrapper_end,
    render_section_wrapper_start,
    show_result_images,
    render_ticket,
    render_qr_code,
)

APP_DIR = Path(__file__).resolve().parent
ASSETS_DIR = APP_DIR / "assets"
BACKGROUND_PATH = ASSETS_DIR / "parking-bg.jpg"
LOGO_PATH = ASSETS_DIR / "school-logo.png"

def main():
    st.set_page_config(page_title="Hệ thống nhận diện biển số xe máy", page_icon="🏍️", layout="wide")
    init_db()
    render_custom_css(APP_TITLE, BACKGROUND_PATH, LOGO_PATH)

    df_logs = fetch_logs()
    active_tickets = get_active_tickets()

    with st.sidebar:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), use_container_width=True)
        st.markdown("### Điều hướng")
        mode = st.radio("Chế độ", ["Xe vào", "Xe ra", "Nhật ký", "Thống kê"], label_visibility="collapsed")
        selected_detector_model = None

        st.markdown("---")
        st.markdown("### Thông tin hệ thống")
        st.caption("Trường ĐH GTVT TP.HCM")
        st.caption("Mô hình: fast-alpr + EasyOCR")
        st.caption(f"Cập nhật: {datetime.now().strftime('%d/%m/%Y %H:%M')}")


    render_dashboard_shell_start()
    render_dashboard_metrics(df_logs)

    if mode == "Xe vào":
        content_left, content_right = st.columns([1, 1], gap="medium")
        with content_left:
            render_section_wrapper_start()
            render_panel_header("Ghi nhận xe vào", "Tải ảnh biển số hoặc chụp trực tiếp từ camera.", "Entry")
            
            input_source = st.radio("Nguồn ảnh", ["Tải tệp", "Máy ảnh"], horizontal=True, label_visibility="collapsed")
            if input_source == "Tải tệp":
                uploaded_entry = st.file_uploader("Chọn ảnh biển số", type=["jpg", "jpeg", "png"], key="entry_upload")
            else:
                uploaded_entry = st.camera_input("Chụp ảnh biển số", key="entry_camera")

            if uploaded_entry is not None:
                current_entry_name = getattr(uploaded_entry, "name", "camera_capture.jpg")
                if st.session_state.get("entry_upload_name") != current_entry_name:
                    st.session_state["entry_upload_name"] = current_entry_name
                    st.session_state["entry_ticket_id"] = None
                try:
                    original_path = save_uploaded_file(uploaded_entry, "entry")
                    with st.spinner("Đang nhận diện biển số..."):
                        processed = process_plate_image(original_path, detector_model=selected_detector_model)
                    ocr = processed.ocr
                    
                    # Auto-confirm logic (90% threshold)
                    is_confident = ocr.get("confidence", 0) > 0.9
                    if is_confident:
                        st.toast(f"✅ Nhận diện chính xác cao: {ocr.get('text')}", icon="🚀")
                    
                    render_ocr_result(ocr)
                    if not ocr.get("is_usable", False) and ocr.get("text"):
                        st.warning(ocr.get("quality_note", "Kết quả OCR chưa đủ tin cậy"))
                    
                    manual_entry_plate = st.text_input(
                        "Biển số chỉnh tay nếu OCR chưa chuẩn",
                        value=ocr.get("text", ""),
                        key="manual_entry_plate",
                        help="Tự động điền từ kết quả OCR"
                    ).strip()
                    effective_entry_plate = manual_entry_plate or ocr.get("text", "")
                    render_capture_details(
                        plate_text=effective_entry_plate,
                        captured_at=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                        ticket_id=st.session_state.get("entry_ticket_id"),
                    )
                    st.session_state["entry_preview"] = (original_path, ocr["annotated_path"])
                except ValidationError as exc:
                    st.error(str(exc))
            render_section_wrapper_end()
        with content_right:
            render_section_wrapper_start()
            render_panel_header("Xem trước và xác nhận", "Quan sát ảnh gốc, ảnh nhận diện và hoàn tất thao tác trong cùng một khung.", "Preview")
            preview = st.session_state.get("entry_preview")
            if preview:
                show_result_images(*preview)
                if st.button("Xác nhận xe vào", key="confirm_entry", use_container_width=True):
                    entry_plate_to_save = (st.session_state.get("manual_entry_plate") or ocr.get("text", "")).strip()
                    result = confirm_vehicle_entry(
                        entry_plate_to_save,
                        image_path=original_path,
                        detected_path=ocr["annotated_path"],
                        plate_path=None,
                        ocr_confidence=ocr["confidence"],
                    )
                    if result.get("success"):
                        st.session_state["entry_ticket_id"] = result.get("ticket_id")
                        st.toast("Ghi nhận xe vào thành công!", icon="🏢")
                        st.rerun()
                    else:
                        st.error(result.get("message", "Không thể ghi nhận xe vào"))
                entry_ticket_id = st.session_state.get("entry_ticket_id")
                if entry_ticket_id:
                    col_t1, col_t2 = st.columns([1, 1])
                    with col_t1:
                        render_ticket(entry_ticket_id)
                    with col_t2:
                        render_qr_code(entry_ticket_id)
            render_section_wrapper_end()
    elif mode == "Xe ra":
        content_left, content_right = st.columns([1, 1], gap="medium")
        with content_left:
            render_section_wrapper_start()
            render_panel_header("Ghi nhận xe ra", "Chọn vé đang hoạt động, tải ảnh biển số và xác nhận xe ra bãi.", "Exit")
            if active_tickets.empty:
                st.info("Không có xe trong bãi")
            else:
                ticket_options = {f"{row['ticket_id']} — {row['plate_entry']}": row["ticket_id"] for _, row in active_tickets.iterrows()}
                selected_label = st.selectbox("Chọn vé", list(ticket_options.keys()))
                selected_ticket = ticket_options[selected_label]
                
                input_source_exit = st.radio("Nguồn ảnh", ["Tải tệp", "Máy ảnh"], horizontal=True, label_visibility="collapsed", key="source_exit")
                if input_source_exit == "Tải tệp":
                    uploaded_exit = st.file_uploader("Chọn ảnh biển số", type=["jpg", "jpeg", "png"], key="exit_upload")
                else:
                    uploaded_exit = st.camera_input("Chụp ảnh biển số", key="exit_camera")

                if uploaded_exit is not None:
                    current_exit_name = getattr(uploaded_exit, "name", "")
                    if st.session_state.get("exit_upload_name") != current_exit_name:
                        st.session_state["exit_upload_name"] = current_exit_name
                    try:
                        original_path = save_uploaded_file(uploaded_exit, "exit")
                        processed = process_plate_image(original_path, detector_model=selected_detector_model)
                        ocr = processed.ocr
                        render_ocr_result(ocr)
                        if not ocr.get("is_usable", False) and ocr.get("text"):
                            st.warning(ocr.get("quality_note", "Kết quả OCR chưa đủ tin cậy"))
                        manual_exit_plate = st.text_input(
                            "Biển số chỉnh tay nếu OCR chưa chuẩn",
                            value=ocr.get("text", ""),
                            key="manual_exit_plate",
                        ).strip()
                        effective_exit_plate = manual_exit_plate or ocr.get("text", "")
                        render_capture_details(
                            plate_text=effective_exit_plate,
                            captured_at=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                            ticket_id=selected_ticket,
                        )
                        st.session_state["exit_preview"] = (original_path, ocr["annotated_path"])
                    except ValidationError as exc:
                        st.error(str(exc))
            render_section_wrapper_end()
        with content_right:
            render_section_wrapper_start()
            render_panel_header("Ảnh và đối chiếu", "Kiểm tra ảnh nhận diện trước khi xác nhận xe ra.", "Verify")
            preview = st.session_state.get("exit_preview")
            if preview:
                show_result_images(*preview)
                if st.button("Xác nhận xe ra", key="confirm_exit", use_container_width=True):
                    exit_plate_to_save = (st.session_state.get("manual_exit_plate") or ocr.get("text", "")).strip()
                    result = confirm_vehicle_exit(
                        selected_ticket,
                        exit_plate_to_save,
                        image_path=original_path,
                        detected_path=ocr["annotated_path"],
                        plate_path=None,
                        ocr_confidence=ocr["confidence"],
                    )
                    if result.get("success"):
                        st.rerun()
                    else:
                        st.error(result["message"])
                render_ticket(selected_ticket)
            render_section_wrapper_end()
    elif mode == "Nhật ký":
        st.markdown("<div class='log-grid'>", unsafe_allow_html=True)
        render_section_wrapper_start()
        render_panel_header("Nhật ký xe ra vào", "Theo dõi toàn bộ lịch sử vé, trạng thái xe và kết quả đối chiếu biển số.", "Logs")
        render_logs_table(df_logs)
        render_section_wrapper_end()
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        render_analytics_dashboard(df_logs)

    render_dashboard_shell_end()


if __name__ == "__main__":
    main()

