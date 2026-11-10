"""
AI Bill & Expense Analyzer - Application Runner.
Executes Streamlit web dashboard.
"""
import sys
import subprocess
from pathlib import Path

def run_app():
    main_script = Path(__file__).resolve().parent / "app" / "main.py"
    cmd = [sys.executable, "-m", "streamlit", "run", str(main_script)]
    print(f"Launching AI Bill & Expense Analyzer on Streamlit...")
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nApplication stopped by user.")

if __name__ == "__main__":
    run_app()
