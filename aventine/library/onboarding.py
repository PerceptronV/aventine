import os
import gdown
import tarfile
from pathlib import Path

from aventine.library.config import INDEX_DATA_GID, QUICKSTART_DOCUMENTS


def download(
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


def quickstart(
        sources_dir: Path = 'aventine/data',
        index_dir: Path = 'aventine/data/dumps',
        tool_dir: Path ='aventine/tools/bin'
    ):
    print('Beginning indexing of all sources in `config.QUICKSTART_DOCUMENTS`. This may take a while...\n')

    from aventine.library.files import perseus_xml_get, perseus_xml2txt
    from aventine.library.index import preprocess
    from aventine.library.wordvec import train_word2vec_model, MultiCorpus

    for doc in QUICKSTART_DOCUMENTS:
        metadata = perseus_xml_get(QUICKSTART_DOCUMENTS[doc], sources_dir)
        metadata = perseus_xml2txt(metadata, sources_dir)
        preprocess(metadata, index_dir, tool_dir=tool_dir)
        pass
    
    print('\nGenerating overall word embeddings. This may take a while...')
    model = train_word2vec_model(MultiCorpus(index_dir))
    model.save(os.path.join(index_dir, 'root', 'word2vec.model'))

    print('\nIndexing complete!')
