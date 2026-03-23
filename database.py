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
            conn = psycopg2.connect(**self.config)
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                if cur.description:
                    result = cur.fetchall()
                conn.commit()
        except Exception as e:
            print(f"Ошибка БД: {e}", flush=True)
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()
        return result

    def get_next_pending_task(self):
        FLASK_URL = os.getenv("FLASK_URL", "https://upura-test-server-production.up.railway.app")
        PHOTOS_DIR = os.getenv("PHOTOS_DIR", "/app/uploads/photos")

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
        filename = row['original_photo_path']
        local_path = os.path.join(PHOTOS_DIR, filename)
        os.makedirs(PHOTOS_DIR, exist_ok=True)

        # Download photo from Flask
        try:
            import requests
            url = f"{FLASK_URL}/api/photos/file/{filename}"
            print(f"Downloading photo from: {url}", flush=True)
            response = requests.get(url)
            if response.status_code == 200:
                with open(local_path, 'wb') as f:
                    f.write(response.content)
                print(f"✅ Photo downloaded: {filename}", flush=True)
            else:
                print(f"❌ Failed to download: {response.status_code}", flush=True)
        except Exception as e:
            print(f"❌ Download error: {e}", flush=True)

        return PhotoTask(
            id=str(row['id']),
            user_id=str(row['user_id']),
            device_id=row['device_id'],
            original_photo_path=local_path,
            status=row['status'],
            meta=row.get('meta')
        )

    def update_status(self, task_id, status):
        query = "UPDATE photo_tasks SET status = %s, updated_at = now() WHERE id = %s::uuid;"
        self.execute_query(query, (status, task_id))
