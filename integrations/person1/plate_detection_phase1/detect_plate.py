import os
import cv2
from ultralytics import YOLO

MODEL_PATH = "license_plate.pt"
INPUT_DIR = "test_images"
OUTPUT_DIR = "results"
CONF_THRESHOLD = 0.25

model = YOLO(MODEL_PATH)


def detect_plate(image):
    boxed_image = image.copy()
    plate_image = None

    best_box = None
    best_conf = -1.0

    results = model(image)

    for result in results:
        boxes = result.boxes
        if boxes is None:
            continue

        for box in boxes:
            conf = float(box.conf[0])

            if conf < CONF_THRESHOLD:
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0])

            if conf > best_conf:
                best_conf = conf
                best_box = (x1, y1, x2, y2)

    if best_box is not None:
        x1, y1, x2, y2 = best_box

        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(image.shape[1], x2)
        y2 = min(image.shape[0], y2)

        cv2.rectangle(boxed_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(
            boxed_image,
            f"Plate {best_conf:.2f}",
            (x1, max(y1 - 10, 20)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )

        plate_image = image[y1:y2, x1:x2]

    return boxed_image, plate_image


def process_image(image_path):
    image = cv2.imread(image_path)

    if image is None:
        print(f"[ERROR] Khong doc duoc anh: {image_path}")
        return

    boxed_image, plate_image = detect_plate(image)

    file_name = os.path.basename(image_path)
    name, ext = os.path.splitext(file_name)

    boxed_output_path = os.path.join(OUTPUT_DIR, f"{name}_boxed{ext}")
    cv2.imwrite(boxed_output_path, boxed_image)

    if plate_image is not None and plate_image.size > 0:
        plate_output_path = os.path.join(OUTPUT_DIR, f"{name}_plate{ext}")
        cv2.imwrite(plate_output_path, plate_image)
        print(f"[OK] {file_name}: da luu anh boxed va anh crop")
    else:
        print(f"[WARN] {file_name}: khong detect duoc bien so")


def main():
    print("=== BAT DAU CHAY PHASE 1 ===")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if not os.path.exists(INPUT_DIR):
        print(f"[ERROR] Khong tim thay thu muc {INPUT_DIR}")
        return

    image_files = [
        f for f in os.listdir(INPUT_DIR)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ]

    print(f"Thu muc input: {INPUT_DIR}")
    print(f"Thu muc output: {OUTPUT_DIR}")
    print(f"So anh tim thay: {len(image_files)}")

    if not image_files:
        print("[ERROR] Khong co anh nao trong test_images")
        return

    for index, file_name in enumerate(image_files, start=1):
        print(f"[{index}/{len(image_files)}] Dang xu ly: {file_name}")
        image_path = os.path.join(INPUT_DIR, file_name)
        process_image(image_path)

    print("=== HOAN TAT PHASE 1 ===")


if __name__ == "__main__":
    main()