import subprocess
import sys
from pathlib import Path

def run_streamlit_app():
    """Launch streamlit app after LangGraph completes."""
    app_path = Path("../.venv/app.py")

    if not app_path.exists():
        raise FileNotFoundError("❌ Streamlit app.py not found!")

    # Launch Streamlit in a separate background process
    subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "app.py", "--server.runOnSave=true"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    print("🚀 Streamlit Dashboard Launched Automatically!")
