import os
import uuid

import cv2

from database import Database
from dataclass import PhotoTask  # Предполагаем, что твой файл называется dataclass.py
from final_step import finalize_task
from pipeline_func import run_cv_pipeline  # Предполагаем, что функции пайплайна в pipeline.py

db = Database()
def main():
    # 1. Настройка пути к тестовому файлу
    test_image_path = r"C:\Users\vwork\PycharmProjects\upura_test_pipeline\test\test_task_001_1_roi.jpg"  # Замени на свой файл
    task_id =str(uuid.uuid4())

    if not os.path.exists(test_image_path):
        print(f"Ошибка: Файл не найден по пути {test_image_path}")
        return

    # 2. Имитация данных из БД
    task = PhotoTask(
        id=task_id,
        user_id="manual_test_user",
        device_id="test_device",
        original_photo_path=test_image_path,
        status="pending",
        meta={"type": "experiment_v1"}
    )

    print(f"Запуск пайплайна для задачи {task_id}...")

    # 3. Запуск обработки
    try:
        task = run_cv_pipeline(task)
        print("Обработка завершена успешно!")

        # 4. Вывод результатов для проверки
        print(f"--- Результаты анализа ---")
        print(f"Количество бактерий: {task.bacteria_count}")
        print(f"Оценка поверхности (1-100): {task.surface_analysis_score}")
        print(f"Найдено колоний: {len(task.colonies_details)}")

        # Вывод информации о первой колонии (если есть)
        if task.colonies_details:
            print(f"Пример первой колонии: {task.colonies_details[0]['description']}")
            print(f"Доминирующий цвет: {task.colonies_details[0].get('dominant_color')}")

        print(f"Результаты дебага сохранены в папку 'debug_photos'")
        finalize_task(task,db)
    except Exception as e:
        print(f"Критическая ошибка пайплайна: {e}")


if __name__ == "__main__":
    main()