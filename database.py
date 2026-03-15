import os

import psycopg2
from psycopg2.extras import RealDictCursor

from dataclass import PhotoTask


class Database:
    def __init__(self):
        self.config = {
   	 "dbname": os.getenv("DB_NAME", "postgres"),
   	 "user": os.getenv("DB_USER", "postgres"),
   	 "password": os.getenv("DB_PASSWORD", "postgres"),
   	 "host": os.getenv("DB_HOST", "localhost"),
   	 "port": os.getenv("DB_PORT", "5432")
	}

    def execute_query(self, query, params=None):
        conn = None
        result = None
        try:
            # Устанавливаем соединение
            conn = psycopg2.connect(**self.config)
            # RealDictCursor позволяет получать данные в виде словаря {'column': value}
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)

                # Если это SELECT, забираем данные
                if cur.description:
                    result = cur.fetchall()

                conn.commit()
        except Exception as e:
            print(f"Ошибка БД: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()
        return result

    def get_pending_tasks(self):
        query = """
        SELECT 
            t.*,
            (SELECT processed_photo_path 
             FROM photo_tasks 
             WHERE device_id = t.device_id 
               AND user_id = t.user_id 
               AND status = 'done' 
               AND id != t.id
             ORDER BY updated_at DESC 
             LIMIT 1) as last_processed_photo
        FROM photo_tasks t
        WHERE t.status = 'pending';
        """
        rows = self.execute_query(query)

        if not rows:
            return []

        # Преобразование словарей в объекты PhotoTask
        return [
            PhotoTask(
                id=str(row['id']),
                user_id=str(row['user_id']),
                device_id=row['device_id'],
                original_photo_path=row['original_photo_path'],
                status=row['status'],
                meta=row['meta'],
                last_processed_photo=row.get('last_processed_photo')
            ) for row in rows
        ]

    def get_next_pending_task(self):
        """Берет задачу и дополняет путь к фото."""
        # Базовая папка, где лежат оригиналы фото
	# BASE_PHOTO_DIR = r"C:\Users\vwork\PycharmProjects\upura_test_server\uploads\photos"
        BASE_PHOTO_DIR = os.getenv("PHOTOS_DIR", "/app/uploads/photos")

        query = """
        UPDATE photo_tasks 
        SET status = 'processing', updated_at = now()
        WHERE id = (
            SELECT id FROM photo_tasks 
            WHERE status = 'pending' 
            ORDER BY created_at ASC 
            LIMIT 1 
            FOR UPDATE SKIP LOCKED
        )
        RETURNING *;
        """
        rows = self.execute_query(query)
        if not rows:
            return None

        row = rows[0]

        # Собираем полный путь.
        # Если в БД лежит имя файла "img_001.jpg", путь станет:
        # C:\Users\vwork\PycharmProjects\upura_test_server\uploads\photos\img_001.jpg
        full_photo_path = os.path.join(BASE_PHOTO_DIR, row['original_photo_path'])

        return PhotoTask(
            id=str(row['id']),
            user_id=str(row['user_id']),
            device_id=row['device_id'],
            original_photo_path=full_photo_path,  # Теперь здесь полный путь
            status=row['status'],
            meta=row.get('meta')
        )

    def update_status(self, task_id, status):
        """Устанавливает статус для конкретной задачи."""
        query = "UPDATE photo_tasks SET status = %s, updated_at = now() WHERE id = %s::uuid;"
        self.execute_query(query, (status, task_id))
