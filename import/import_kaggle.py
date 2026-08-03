import kagglehub
import shutil
from pathlib import Path
# Download latest version
path = Path(kagglehub.dataset_download("suraj520/telecom-churn-dataset"))

dest_path = Path("D:\exercise_for_final_project")

shutil.copytree(path, dest_path, dirs_exist_ok=True)

print(dest_path.resolve())
