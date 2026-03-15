import cv2
import numpy as np
import os
from dataclass import PhotoTask

# Создаем папки, если их нет
DEBUG_DIR = "debug_photos"
OUTPUT_BASE = "uploads/tasks"

os.makedirs(DEBUG_DIR, exist_ok=True)


def run_cv_pipeline(task: PhotoTask) -> PhotoTask:
    """Основной оркестратор пайплайна."""
    img = cv2.imread(task.original_photo_path)
    if img is None:
        raise ValueError(f"Не удалось загрузить изображение: {task.original_photo_path}")

    # 1. Подготовка и ROI
    task = process_initial_stage(task, img)
    cv2.imwrite(os.path.join(DEBUG_DIR, f"{task.id}_1_roi.jpg"), task.last_processed_photo)

    # 2. Анализ покрытия поверхности
    task = analyze_surface_coverage(task)

    # 3. Выделение объектов
    task = extract_colonies_from_mask(task)
    cv2.imwrite(os.path.join(DEBUG_DIR, f"{task.id}_2_mask.jpg"), task.colony_mask)
    cv2.imwrite(os.path.join(DEBUG_DIR, f"{task.id}_3_result.jpg"), task.mix_mask_analysis)

    # 4. Этап анализа цвета каждой колонии
    task = analyze_colony_colors(task)
    return task


def analyze_surface_coverage(task: PhotoTask) -> PhotoTask:
    """Вычисляет процент покрытия поверхности бактериями."""
    if task.colony_mask is None:
        return task

    mask_8u = task.colony_mask.astype(np.uint8)
    white_pixels = cv2.countNonZero(mask_8u)
    gray_roi = cv2.cvtColor(task.last_processed_photo, cv2.COLOR_BGR2GRAY)
    total_pixels = cv2.countNonZero(gray_roi)

    coverage = (white_pixels / total_pixels * 100) if total_pixels > 0 else 0
    task.surface_analysis_score = int(min(max(coverage, 1), 100))
    return task


def process_initial_stage(task: PhotoTask, img: np.ndarray) -> PhotoTask:
    h, w = img.shape[:2]
    center, radius = (w // 2, h // 2), min(h, w) // 2

    task.last_processed_photo = img[center[1] - radius:center[1] + radius, center[0] - radius:center[0] + radius]

    inner_radius = int(radius * 0.7)
    mask_size = radius * 2
    inner_mask = np.zeros((mask_size, mask_size), dtype=np.uint8)
    cv2.circle(inner_mask, (radius, radius), inner_radius, 255, -1)

    roi_gray = cv2.cvtColor(task.last_processed_photo, cv2.COLOR_BGR2GRAY)
    _, task.colony_mask = cv2.threshold(cv2.bitwise_and(roi_gray, roi_gray, mask=inner_mask),
                                        139, 255, cv2.THRESH_BINARY)

    task.mix_mask_analysis = cv2.cvtColor(task.colony_mask, cv2.COLOR_GRAY2BGR)
    return task


def extract_colonies_from_mask(task: PhotoTask) -> PhotoTask:
    """Выделение контуров, сохранение кропов в Debug и Output."""
    if task.colony_mask is None:
        return task

    # Пути для сохранения
    task_output_dir = os.path.join(OUTPUT_BASE, str(task.id), "output")
    colonies_output_dir = os.path.join(task_output_dir, "colonies")
    os.makedirs(colonies_output_dir, exist_ok=True)

    task_debug_path = os.path.join(DEBUG_DIR, f"task_{task.id}_colonies")
    os.makedirs(task_debug_path, exist_ok=True)

    contours, _ = cv2.findContours(task.colony_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    task.colonies_details = []
    detection_result_img = task.last_processed_photo.copy()

    for i, contour in enumerate(contours):
        area = cv2.contourArea(contour)
        x, y, w, h = cv2.boundingRect(contour)

        if area > 400 and w > 20 and h > 20:
            colony_crop = task.last_processed_photo[y:y + h, x:x + w]

            # Сохранение в обе точки
            prod_file_name = os.path.join(colonies_output_dir, f"colony_{i}.jpg")
            debug_file_name = os.path.join(task_debug_path, f"colony_{i}.jpg")

            cv2.imwrite(prod_file_name, colony_crop)
            cv2.imwrite(debug_file_name, colony_crop)

            cv2.rectangle(detection_result_img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(detection_result_img, str(i), (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            task.colonies_details.append({
                "image": colony_crop,
                "path": prod_file_name,  # В базу пишем путь к продакшену
                "description": f"Colony_{i}: area={area}"
            })

    # Сохранение маски и результата в обе точки
    cv2.imwrite(os.path.join(task_output_dir, "mask.jpg"), task.colony_mask)
    cv2.imwrite(os.path.join(task_output_dir, "detected.jpg"), detection_result_img)
    cv2.imwrite(os.path.join(DEBUG_DIR, f"{task.id}_4_detected.jpg"), detection_result_img)

    task.bacteria_count = len(task.colonies_details)
    return task


def analyze_colony_colors(task: PhotoTask) -> PhotoTask:
    """Анализирует доминирующий цвет каждой колонии."""
    for colony in task.colonies_details:
        img_crop = colony["image"]
        mean_bgr = cv2.mean(img_crop)[:3]
        dominant_color_rgb = (int(mean_bgr[2]), int(mean_bgr[1]), int(mean_bgr[0]))
        colony["dominant_color"] = dominant_color_rgb
        colony["description"] += f" | color={dominant_color_rgb}"
    return task