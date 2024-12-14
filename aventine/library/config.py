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

ALLOWED_LEMMATA = re.compile(r"[a-zA-Z_\-,.'!/]+")

WWW_EXPR = r"[a-zA-Z1-9,./;()\[\]\s]+\n([a-zA-Z1-9,./();\s]+)"

SENTENCE_TRANSFORMER_MODEL = 'Alibaba-NLP/gte-base-en-v1.5'
