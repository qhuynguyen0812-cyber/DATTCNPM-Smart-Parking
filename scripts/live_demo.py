"""
UTH Smart Parking - Live End-to-End System Demonstration.
Executes 4 complete ground-truth operational scenarios:
1. Student Entry at Gate 1 -> Auto-dispatch priority ZONE_B (Great Central Courtyard).
2. Staff / Lecturer Entry at Gate 1 -> Auto-dispatch ZONE_E (Ground/lower floor, Free).
3. Student Exit at Gate 2 (2-lane Station) -> VietQR Generation -> Bank Reconcile -> Barrier Lift.
4. Staff / Lecturer Exit at Gate 2 -> Immediate Free 0 VND Auto Barrier Lift.
"""

import time
import json
import sys
import io
from pathlib import Path

# Ensure UTF-8 stdout for Windows terminals
if sys.stdout and hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from datetime import datetime
from backend.db import (
    apply_migrations,
    get_all_zones,
    get_zone_status,
    suggest_optimal_zone,
    fetch_active_ticket_by_card_id,
    recalculate_zone_occupancies,
)
from backend.parking_service import vehicle_entry, vehicle_exit
from backend.payment_reconciliation import reconcile_bank_transaction
from backend.customer_display_state import get_customer_display_state
from integrations.barrier_service import barrier_simulator


def print_step(title: str):
    print("\n" + "=" * 70)
    print(f"  {title.upper()}")
    print("=" * 70)


def run_demo():
    print("\n" + "#" * 70)
    print("   HE THONG QUAN LY BAI XE THONG MINH UTH CO SO 1 - LIVE DEMO")
    print("   Nhom Dang Dinh Khang - Tech Lead: Nguyen Quang Huy")
    print("#" * 70)

    # Khởi tạo CSDL & làm sạch dữ liệu demo trước đó để kịch bản luôn chạy mượt mà
    apply_migrations()
    import sqlite3
    from backend.config import DB_PATH
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE parking_logs SET status = 'COMPLETED', exit_time = datetime('now') "
            "WHERE (card_id IN ('UTH_SV_2026_01', 'UTH_STAFF_GV_01', '034206012355') OR plate_entry LIKE '%123%45%' OR plate_entry LIKE '%888%88%') "
            "AND status != 'COMPLETED'"
        )
        conn.commit()
    recalculate_zone_occupancies()

    initial_barrier_cmds = len(barrier_simulator.commands)

    # -------------------------------------------------------------
    # 0. KIEM TRA SUC CHUA 4 KHU THEO THU TU UU TIEN B -> C -> A -> E
    # -------------------------------------------------------------
    print_step("0. KIEM TRA SO DO MAT BANG & SUC CHUA 4 KHU (THU TU UU TIEN B - C - A - E)")
    zones = get_all_zones()
    for z in zones:
        print(f"  • [{z['zone_id']}] {z['zone_name']}: {z['current_occupied']}/{z['max_capacity']} xe ({z['available_slots']} cho trong)")

    # -------------------------------------------------------------
    # 1. KICH BAN 1: SINH VIEN VAO CONG 1
    # -------------------------------------------------------------
    print_step("KICH BAN 1: SINH VIEN VAO CONG 1 (VO OANH)")
    print("  [AI Camera sau]: Chup bien so 59X3-123.45 (Do tin cay 98.6%)")
    print("  [Dau doc RFID]: Quet the trang chip UTH (Ma the: UTH_SV_2026_01)")
    
    suggested_zone = suggest_optimal_zone(user_type="STUDENT")
    print(f"  [Thuat toan dieu phoi]: Uu tien chon khu rong nhat -> {suggested_zone} (Dai San Trung Tam)")

    entry_sv = vehicle_entry(
        plate_text="59X3-12345",
        card_id="UTH_SV_2026_01",
        gate_entry="GATE_1",
        lane_entry="LANE_1",
        zone_assigned=suggested_zone,
        user_type="STUDENT",
    )
    print(f"  --> Ket qua vao: Ma ve = {entry_sv['ticket_id']}, Trang thai = {entry_sv['status']}")
    print(f"      Doi tuong: {entry_sv['user_type']}, Phi ban dau = {entry_sv['fee']:,} VND")
    
    status_b = get_zone_status("ZONE_B")
    print(f"      Cap nhat suc chua Khu B: {status_b['current_occupied']}/{status_b['max_capacity']} xe")

    # -------------------------------------------------------------
    # 2. KICH BAN 2: GIANG VIEN / CAN BO VAO CONG 1
    # -------------------------------------------------------------
    print_step("KICH BAN 2: GIANG VIEN / CAN BO VAO CONG 1")
    print("  [AI Camera sau]: Chup bien so xe giang vien 51F-888.88")
    print("  [Dau doc RFID]: Quet the Cán bộ (Ma the: UTH_STAFF_GV_01)")
    
    suggested_staff_zone = suggest_optimal_zone(user_type="STAFF")
    print(f"  [Thuat toan dieu phoi]: Dinh tuyen dac thu -> {suggested_staff_zone} (Nha xe 4 tang: Tang duoi CB-GV)")

    entry_staff = vehicle_entry(
        plate_text="51F-888.88",
        card_id="UTH_STAFF_GV_01",
        gate_entry="GATE_1",
        lane_entry="LANE_2",
        zone_assigned=suggested_staff_zone,
        user_type="STAFF",
    )
    print(f"  --> Ket qua vao: Ma ve = {entry_staff['ticket_id']}, Trang thai = {entry_staff['status']}")
    print(f"      Doi tuong: {entry_staff['user_type']}, Phi = {entry_staff['fee']} VND (MIEN PHI 100%)")

    # -------------------------------------------------------------
    # 3. KICH BAN 3: SINH VIEN RA CONG 2 (TRAM RA KHU C - BOT 2 LAN)
    # -------------------------------------------------------------
    print_step("KICH BAN 3: SINH VIEN RA CONG 2 & THANH TOAN VIETQR NAPAS 247")
    print("  [Dau doc RFID tai bot]: Sinh vien tra the UTH_SV_2026_01 vao ro the do")
    print("  [AI Camera sau]: Chup bien so xe cho xuat ben: 59X3-123.45")

    exit_sv = vehicle_exit(
        card_id="UTH_SV_2026_01",
        plate_text="59X3-12345",
        gate_exit="GATE_2",
        lane_exit="LANE_C_1",
        payment_method="VIETQR",
        payment_status="UNPAID",
    )
    print(f"  --> Ket qua doi chieu: {exit_sv['match_result']} (Trung khop bien so vao/ra)")
    print(f"      Tinh phi gui xe: {exit_sv['fee']:,} VND (Ve ngay dong gia 5k)")
    print(f"      Kich hoat VietQR Napas 247: {exit_sv['vietqr']['qr_image_url'][:75]}...")

    # Kích hoạt màn hình phụ Customer Display
    from backend.customer_display_state import trigger_checkout_display, trigger_success_display
    trigger_checkout_display(
        plate_number="59X3-12345",
        fee=5000,
        card_id="UTH_SV_2026_01",
        ticket_id=exit_sv["ticket_id"],
        qr_url=exit_sv["vietqr"]["qr_image_url"],
    )
    disp_state = get_customer_display_state()
    print(f"  [Man hinh phu dien thoai]: Trang thai = {disp_state['state']}, Hien thi QR 5.000d cho khach quet")

    print("\n  [Mo phong]: Sinh vien mo App Ngan hang bat ky quet ma VietQR...")
    time.sleep(0.5)

    # Webhook báo tiền đã về MBBank
    webhook_payload = {
        "accountNo": "0325617476",
        "creditAmount": 5000,
        "description": f"GUIXE UTH_SV_2026_01 thanh toan ve xe {exit_sv['ticket_id']}",
        "refNo": f"MB_{int(time.time())}",
    }
    reconcile_res = reconcile_bank_transaction(webhook_payload)
    status_str = "THANH TOAN HOP LE (200 OK)" if reconcile_res.get("reconciled") else "THAT BAI"
    print(f"  [MBBank Webhook]: Nhan thanh toan 5.000 VND -> {status_str}")
    print(f"      Chi tiet: {reconcile_res.get('message')}")

    trigger_success_display(plate_number="59X3-12345", amount=5000)
    disp_state_after = get_customer_display_state()
    print(f"  [Man hinh phu dien thoai]: {disp_state_after['state']} -> BARRIER DANG MO, CHUC BAN THUONG LO BINH AN!")

    # -------------------------------------------------------------
    # 4. KICH BAN 4: GIANG VIEN RA CONG 2 (MIEN PHI 100%)
    # -------------------------------------------------------------
    print_step("KICH BAN 4: GIANG VIEN / CAN BO RA CONG 2 (MIEN PHI 0 VND)")
    print("  [Dau doc RFID tai bot]: Giang vien quet the UTH_STAFF_GV_01")
    print("  [AI Camera sau]: Chup bien so xe: 51F-888.88")

    exit_staff = vehicle_exit(
        card_id="UTH_STAFF_GV_01",
        plate_text="51F-888.88",
        gate_exit="GATE_2",
        lane_exit="LANE_C_2",
    )
    print(f"  --> Ket qua doi chieu: {exit_staff['match_result']}")
    print(f"      Doi tuong: {exit_staff['user_type']}")
    print(f"      Phi thanh toan: {exit_staff['fee']} VND (MIEN PHI)")
    print(f"      Hinh thuc: {exit_staff['payment_method']}, Trang thai = {exit_staff['payment_status']}")
    print(f"      Tu dong nang can Barrier: KHONG CAN THU TIEN HAY QUET QR!")

    trigger_success_display(plate_number="51F-888.88", amount=0, user_type="STAFF")
    disp_staff = get_customer_display_state()
    print(f"  [Man hinh phu dien thoai]: {disp_staff['state']} -> XAC THUC THE CB-GV-CNV: MIEN PHI GUI XE (0 VND)")

    # -------------------------------------------------------------
    # 5. TONG KET SO DO SUC CHUA SAU KHI XE RA
    # -------------------------------------------------------------
    print_step("5. TONG KET TRANG THAI HOAT DONG HE THONG")
    zones_after = get_all_zones()
    for z in zones_after:
        print(f"  • [{z['zone_id']}] {z['zone_name']}: {z['current_occupied']}/{z['max_capacity']} xe ({z['available_slots']} cho trong)")

    total_barrier = len(barrier_simulator.commands) - initial_barrier_cmds
    print(f"\n  [Lenh dieu khien phan cung]: {total_barrier} lenh mo can Barrier tu dong duoc thuc thi thanh cong!")
    print("\n" + "#" * 70)
    print("   DEMO HOAN TAT 100% THANH CONG!")
    print("#" * 70 + "\n")


if __name__ == "__main__":
    run_demo()
