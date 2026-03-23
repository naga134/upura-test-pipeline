import time
import os
import sys

print("--- Starting worker ---", flush=True)

from database import Database
from dataclass import PhotoTask
import final_step
from pipeline_func import run_cv_pipeline

def worker_loop():
    db = Database()
    print("--- [Worker] Waiting for tasks... ---", flush=True)

    while True:
        try:
            task = db.get_next_pending_task()

            if task:
                print(f"[{task.id}] New task found. Processing...", flush=True)
                db.update_status(task.id, 'processing')
                task = run_cv_pipeline(task)
                final_step.finalize_task(task, db)
                print(f"[{task.id}] Task completed!", flush=True)
            else:
                print("No tasks, sleeping 5s...", flush=True)
                time.sleep(5)

        except Exception as e:
            print(f"Error: {e}", flush=True)
            time.sleep(10)

if __name__ == "__main__":
    worker_loop()
