import json
import os
from database import Database
from dataclass import PhotoTask


def finalize_task(task: PhotoTask, db: Database):
    """
    Создает абсолютные пути для всех файлов и сохраняет их в БД и JSON.
    """
    # 1. Получаем абсолютный путь к папке проекта (или задаем базу)
    # Предполагаем, что uploads находится в корне проекта
    base_dir = os.path.abspath("uploads")
    task_output_dir = os.path.join(base_dir, "tasks", str(task.id), "output")

    os.makedirs(task_output_dir, exist_ok=True)

    json_path = os.path.join(task_output_dir, "result.json")

    # Формируем структуру JSON с АБСОЛЮТНЫМИ путями
    json_data = {
        "task_id": str(task.id),
        "analysis_timestamp": "2026-03-12T15:21:00Z",
        "summary": {
            "bacteria_count": task.bacteria_count,
            "surface_analysis_score": task.surface_analysis_score
        },
        "files": {
            "mask_path": os.path.join(task_output_dir, "mask.jpg"),
            "detected_overlay_path": os.path.join(task_output_dir, "detected.jpg")
        },
        "colonies_details": [
            {
                "id": i,
                "path": os.path.abspath(c["path"]),  # Принудительно в абсолютный
                "description": c["description"],
                "ai_analysis": {
                    "predicted_type": "Pending",
                    "confidence": 0.0,
                    "raw_notes": "Ожидает обработки ИИ"
                }
            } for i, c in enumerate(task.colonies_details)
        ]
    }

    # Запись JSON на диск
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=4, ensure_ascii=False)

    # Обновление БД (записываем абсолютный путь к JSON)
    query = """
    UPDATE photo_tasks SET
        status = 'done',
        updated_at = now(),
        processed_photo_path = %s,
        bacteria_count = %s,
        fungi_count = %s,
        pathogens_count = %s,
        microbiome_score = %s,
        surface_analysis_score = %s
    WHERE id = %s::uuid;
    """

    params = (
        json_path,  # Абсолютный путь к result.json
        task.bacteria_count,
        10,
        10,
        10,
        task.surface_analysis_score,
        str(task.id)
    )

    db.execute_query(query, params)

    print(f"Задача {task.id} обработана.")
    print(f"Абсолютный путь JSON: {json_path}")