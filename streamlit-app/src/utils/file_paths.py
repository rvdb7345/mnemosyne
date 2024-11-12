import os
from pathlib import Path

import git
import sys

# from python_helper import get_project_logger
#
# logger = get_project_logger(logger_name=__name__)

def get_project_path() -> Path:
    """Get the path to the project directory. Function serves to harmonise referencing of files.

    Returns:
        Project path.
    """
    git_repo = git.Repo(os.getcwd(), search_parent_directories=True)
    git_root = git_repo.git.rev_parse("--show-toplevel")

    return Path(git_root)

def add_project_to_path(project_path_obj=None):
    """Add project folder to path using the ProjectPaths."""
    if project_path_obj is None:
        project_path_obj = ProjectPaths()

    # add project folder to path
    try:
        sys.path.insert(0, str(project_path_obj.PROJECT_DIR))
    except Exception as e:
        print(e)


class ProjectPaths:
    try:
        PROJECT_DIR = get_project_path()
    except Exception as e:
        PROJECT_DIR = Path(__file__).parents[1]
        # logger.warning(f"Could not retrieve Git project directory, using {PROJECT_DIR} as project directory.")

    DATA_DIR = PROJECT_DIR.joinpath("data")
    PYTHON_UTILS_DIR = PROJECT_DIR.joinpath("python_utils")
    CONFIG_DIR = PROJECT_DIR.joinpath("config")
    MODELS_DIR = PROJECT_DIR.joinpath("models")
    ENV_FILE = CONFIG_DIR.joinpath(".env")

    # make directories
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
    Path(PYTHON_UTILS_DIR).mkdir(parents=True, exist_ok=True)
    Path(CONFIG_DIR).mkdir(parents=True, exist_ok=True)
    Path(MODELS_DIR).mkdir(parents=True, exist_ok=True)


