import os
import gdown
import tarfile
from pathlib import Path

from aventine.library.config import INDEX_DATA_GID


def run(
        data_dir: Path = 'aventine/data'
    ):

    data_dir = Path(data_dir)
    os.makedirs(data_dir, exist_ok=True)
    url = f'https://drive.google.com/uc?id={INDEX_DATA_GID}'
    tar_fpath = str(data_dir / 'data.tar.gz')

    gdown.download(url, tar_fpath, quiet=False)
    with tarfile.open(tar_fpath, "r:gz") as tar:
        tar.extractall(path=data_dir)
    
    os.remove(tar_fpath)
