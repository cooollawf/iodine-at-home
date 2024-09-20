from git.repo import Repo
from core.config import config
import os
download_path = os.path.join(config.get('download_path'))

Repo.clone_from(url=config.get('git_repo.url'),to_path=download_path,branch=config.get('git_repo.branch'))