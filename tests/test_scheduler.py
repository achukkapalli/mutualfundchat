import os
import sys
import time

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.scheduler import InProcessScheduler

def test_scheduler_lifecycle():
    print("\n--- Testing In-Process Scheduler Lifecycle ---")
    
    # Initialize scheduler with a short test log path and 1 hour refresh interval
    scheduler = InProcessScheduler(interval_seconds=3600, log_path="data/test_scheduler.log")
    
    status = scheduler.get_status()
    assert status["is_alive"] is False, "Scheduler thread should not be active initially"
    assert status["last_run"] == "Never", "Scheduler last_run should be 'Never'"
    
    print("  Starting scheduler...")
    scheduler.start()
    
    # Let thread initialize
    time.sleep(0.5)
    
    status = scheduler.get_status()
    assert status["is_alive"] is True, "Scheduler thread failed to start/become alive"
    assert status["next_run"] != "Not Scheduled", "Scheduler next_run not configured"
    print(f"  Scheduler status: {status}")
    print("  >>> Scheduler successfully running in background.")
    
    print("  Stopping scheduler...")
    scheduler.stop()
    
    status = scheduler.get_status()
    assert status["is_alive"] is False, "Scheduler thread was not stopped cleanly"
    print("  >>> Scheduler successfully stopped.")
    
    # Cleanup test log
    if os.path.exists("data/test_scheduler.log"):
        os.remove("data/test_scheduler.log")
        
    print("\nAll scheduler tests passed successfully!")

if __name__ == "__main__":
    test_scheduler_lifecycle()
