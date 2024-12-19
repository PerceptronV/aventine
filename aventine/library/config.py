import re

import cltk

from aventine.library.utils import LargeDict


ROOT_FINGERPRINT = {
    'lemmatised': str,
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
    'corpus_lemmata_info': dict
}

SENTENCE_TRANSFORMER_MODEL = 'Alibaba-NLP/gte-base-en-v1.5'
WORD_EMBEDDING_MODEL = cltk.embeddings.embeddings.Word2VecEmbeddings

SMALL_SEP = ' '
CHUNK_SEP = '\n'

ALLOWED_PUNCTS = r",.?!()"
ALLOWED_SYMBOLS = r"a-zA-Z" + ALLOWED_PUNCTS + r" \n"

ALLOWED_LEMMATA = re.compile(r"[a-zA-Z]+")
BAD_LEMMATA = {'con', 'unietvicensimus'}

###############################

QUICKSTART_DOCUMENTS = {
    'Aeneid': '1999.02.0055',
    'Georgicon': '1999.02.0059',
    'Naturalis Historia': '1999.02.0138',
    'Annales': '1999.02.0077',
    'Historiae': '1999.02.0079',
    'Carmina': '1999.02.0003',
    'Metamorphoses': '1999.02.0029'
}
