import time
import os
from database import Database
from dataclass import PhotoTask
import final_step
from pipeline_func import run_cv_pipeline


def worker_loop():
    db = Database()
    print("--- [Worker] Запущен и ожидает задачи... ---")

    while True:
        try:
            # 1. Получаем задачу со статусом 'pending'
            # Предполагаем, что метод возвращает объект PhotoTask или None
            task = db.get_next_pending_task()

            if task:
                print(f"[{task.id}] Обнаружена новая задача. Начало обработки.")

                # Обновляем статус на 'processing', чтобы другие воркеры не взяли её
                db.update_status(task.id, 'processing')

                # 2. Выполнение пайплайна
                task = run_cv_pipeline(task)

                # 3. Дополнение данными для ИИ (наш новый этап)
                #task = analyze_colonies_metadata(task)

                # 4. Финализация (сохранение result.json и обновление БД)
                final_step.finalize_task(task, db)

                print(f"[{task.id}] Задача успешно завершена.")
            else:
                # Если задач нет, отдыхаем 5 секунд
                time.sleep(5)

        except Exception as e:
            print(f"Критическая ошибка при обработке: {e}")
            # Опционально: db.update_status(task.id, 'failed') если id доступен
            time.sleep(10)  # Пауза при ошибке


if __name__ == "__main__":
    worker_loop()