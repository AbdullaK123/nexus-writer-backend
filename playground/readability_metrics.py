import sys
from pathlib import Path

# Ensure the project root is on sys.path before importing from `app`
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.agents.models import ReadabilityMetrics


if __name__ == "__main__":
    text = "This is a sample text for readability metrics."
    metrics = ReadabilityMetrics.from_text(text)
    print(metrics)
