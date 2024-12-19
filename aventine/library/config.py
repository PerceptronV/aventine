import re

from aventine.library.utils import LargeDict


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

SMALL_SEP = ' '
CHUNK_SEP = '\n'

ALLOWED_PUNCTS = r",.?!()"
ALLOWED_SYMBOLS = r"a-z" + ALLOWED_PUNCTS + r" \n"

ALLOWED_LEMMATA = re.compile(r"[a-zA-Z]+")
BAD_LEMMATA = {'con', 'unietvicensimus'}

WORD2VEC_EPOCHS = 30
WORD2VEC_DIMS = 300

###############################

INDEX_DATA_GID = '1O81jdGmR0VTiomsQVagX6OalOsTtClrB'

QUICKSTART_DOCUMENTS = {
    'Aeneid': '1999.02.0055',
    'Georgicon': '1999.02.0059',
    'Naturalis Historia': '1999.02.0138',
    'Annales': '1999.02.0077',
    'Historiae': '1999.02.0079',
    'Carmina': '1999.02.0003',
    'Metamorphoses': '1999.02.0029'
}
