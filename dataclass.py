import numpy as np
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

@dataclass
class PhotoTask:
    # Исходные данные из БД
    id: str
    user_id: str
    device_id: Optional[str]
    original_photo_path: str
    status: str
    meta: Optional[dict]

    # Контекст
    last_processed_photo: Optional[Any] = None  # Изображение (ROI чашки)
    last_processed_photo_path: Optional[str] = None # Путь к файлу

    # Результаты анализа
    bacteria_count: int = 0
    fungi_count: int = 0
    pathogens_count: int = 0
    microbiome_score: int = 0
    surface_analysis_score: int = 0

    # Маски и изображения
    colony_mask: Optional[Any] = None       # Изображение маски
    colony_mask_path: Optional[str] = None  # Путь к файлу маски
    mix_mask_analysis: Optional[Any] = None # Результирующее фото с наложением
    prev_colony_mask_path: Optional[str] = None

    # Список объектов: описание колоний
    # Формат: [{"image": object, "description": str}, ...]
    colonies_details: List[Dict[str, Any]] = field(default_factory=list)