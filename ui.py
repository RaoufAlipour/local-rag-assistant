"""Arayüzü loopback üzerinde başlatır; çalışma dizininden bağımsızdır."""
from pathlib import Path
import os
import sys


def main():
    try:
        from streamlit.web import cli
    except ImportError:
        print("Önce kurun: python -m pip install -r requirements-ui.txt")
        return 1
    root = Path(__file__).resolve().parent
    os.chdir(root)
    sys.argv = ["streamlit", "run", str(root / "app.py"),
                "--global.developmentMode=false",
                "--server.address=127.0.0.1", "--server.port=8501",
                "--browser.gatherUsageStats=false", "--server.fileWatcherType=none",
                "--theme.base=dark", "--theme.primaryColor=#a6baff",
                "--theme.backgroundColor=#080808", "--theme.secondaryBackgroundColor=#1c1c1c"]
    return cli.main()


if __name__ == "__main__":
    raise SystemExit(main())
