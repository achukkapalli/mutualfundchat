import time
import threading
import os
import sys
from datetime import datetime

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.data.ingest import DataIngestionPipeline

class InProcessScheduler:
    def __init__(self, interval_seconds=86400, log_path="data/scheduler.log"):
        self.interval = interval_seconds
        self.log_path = log_path
        self.pipeline = DataIngestionPipeline()
        self.thread = None
        self.stop_event = threading.Event()
        self.last_run = None
        self.next_run = None
        
        # Ensure log directory exists
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

    def log(self, message):
        """Appends log messages to the scheduler log file with timestamps."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] {message}\n"
        print(f"[Scheduler] {message}")
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(log_line)
        except Exception as e:
            print(f"[Scheduler] Failed to write log: {e}")

    def _run_loop(self):
        self.log("Background scheduler daemon thread started.")
        self.next_run = datetime.fromtimestamp(time.time() + self.interval)
        
        while not self.stop_event.is_set():
            # Wait for interval or stop event
            stopped = self.stop_event.wait(self.interval)
            if stopped:
                break
            
            self.log("Waking up to execute periodic data ingestion...")
            try:
                # Use incremental indexing (force_reindex=False) so we only process changed data
                self.pipeline.run(force_reindex=False)
                self.last_run = datetime.now()
                self.log("Ingestion ran successfully.")
            except Exception as e:
                self.log(f"[ERROR] Periodic ingestion failed: {str(e)}")
            
            self.next_run = datetime.fromtimestamp(time.time() + self.interval)
            self.log(f"Next scheduled run at: {self.next_run.strftime('%Y-%m-%d %H:%M:%S')}")

    def start(self):
        """Spawns and starts the daemon thread if it is not already running."""
        if self.thread is None or not self.thread.is_alive():
            self.stop_event.clear()
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()
            self.log("Scheduler started.")

    def stop(self):
        """Signals the background thread to stop and waits for it to join."""
        if self.thread and self.thread.is_alive():
            self.log("Stopping scheduler...")
            self.stop_event.set()
            self.thread.join(timeout=5)
            self.log("Scheduler stopped successfully.")
            
    def get_status(self):
        """Returns scheduler status dict for UI consumption."""
        return {
            "is_alive": self.thread.is_alive() if self.thread else False,
            "last_run": self.last_run.strftime("%Y-%m-%d %H:%M:%S") if self.last_run else "Never",
            "next_run": self.next_run.strftime("%Y-%m-%d %H:%M:%S") if self.next_run else "Not Scheduled",
            "log_path": self.log_path
        }
