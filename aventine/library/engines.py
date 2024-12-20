from aventine.library.params import SOURCES_DIR, INDEX_DIR, TOOL_DIR
from aventine.library.search import AventineSearch

default_engine = AventineSearch(
    sources_dir=SOURCES_DIR,
    index_dir=INDEX_DIR,
    tool_dir=TOOL_DIR
)
