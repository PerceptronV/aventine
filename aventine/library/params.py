import re
import os

from aventine.library.utils import LargeDict


SMALL_SEP = ' '
CHUNK_SEP = '\n'
ALLOWED_PUNCTS = r",.?!()"
ALLOWED_SYMBOLS = r"a-z" + ALLOWED_PUNCTS + r" \n"

ALLOWED_LEMMATA = re.compile(r"[a-z]+")
BAD_LEMMATA = {'con', 'unietvicensimus'}

###############################

DATA_DIR = 'aventine/data'
SOURCES_DIR = os.path.join(DATA_DIR, 'sources')
INDEX_DIR = os.path.join(DATA_DIR, 'dumps')
TOOL_DIR = 'aventine/tool/bin'

ROOT_FINGERPRINT = {
    'lemmata_arr': list,
    'lat_embeddings': list,
    'definitions': list,
    'eng_embeddings': list,
    'root_lemmata_info': LargeDict,
    'existing_lemmata': set,
    'info': dict
}
CORPUS_FINGERPRINT = {
    'meta': dict,
    'lemmatised': str,
    'corpus_lemmata_info': dict
}

WORD2VEC_EPOCHS = 30
WORD2VEC_DIMS = 300

###############################

INDEX_DATA_GID = '1M-lNKVDhXH0j24CQW2FEW_cD4XHRNKx-'

QUICKSTART_DOCUMENTS = {
    'Aeneid': '1999.02.0055',
    'Georgicon': '1999.02.0059',
    'Naturalis Historia': '1999.02.0138',
    'Annales': '1999.02.0077',
    'Historiae': '1999.02.0079',
    'Carmina': '1999.02.0003',
    'Metamorphoses': '1999.02.0029'
}

MODE = 'INDEX'      # 'INDEX' or 'SEARCH'
