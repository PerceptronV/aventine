import re

from utils import LargeDict


ROOT_FINGERPRINT = {
    'existing_lemmata': set,
    'lemmata_arr': list,
    'definitions': list,
    'lat_embeddings': list,
    'eng_embeddings': list,
    'root_lemmata_info': LargeDict,
    'info': dict
}

CORPUS_FINGERPRINT = {
    'meta': dict,
    'corpus_lemmata_info': LargeDict
}

SENTENCE_TRANSFORMER_MODEL = 'Alibaba-NLP/gte-base-en-v1.5'

ALLOWED_LEMMATA = re.compile(r"[a-zA-Z_\-,.'!/]+")

WWW_EXPR = r"[a-zA-Z1-9,./;()\[\]\s]+\n([a-zA-Z1-9,./();\s]+)"

CHUNK_SEP = '\n'

###############################

QUICKSTART_DOCUMENTS = {
    'Aeneid': '1999.02.0055',
    'Naturalis Historia': '1999.02.0138',
    'Georgicon': '1999.02.0059',
    'Annales': '1999.02.0077',
    'Metamorphoses': '1999.02.0029',
    'De bello Gallico': '1999.02.0002',
    'Carmina': '1999.02.0003',
    'Historiae': '1999.02.0079',
    'Tristia': '2008.01.0492',
    'De Bello Civili': '1999.02.0075',
    'Ex Ponto': '2008.01.0493'
}
