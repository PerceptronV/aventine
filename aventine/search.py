from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from aventine.library.engines import default_engine as engine

bp = Blueprint('search', __name__, url_prefix='/search')

@bp.route('/')
def search():
    query = request.args.get('query')
    language = request.args.get('language').strip()
    if request.args.get('texts') is None or request.args.get('texts') == 'ALL':
        texts = None
    else:
        texts = {i.strip() for i in request.args.get('texts').split(',')}
    results = int(n) if (n := request.args.get('results')) is not None else 50

    data = engine.search(query=query,
                         language=language,
                         texts=texts,
                         results=results)
    g.query = query
    g.language = language
    g.texts = ', '.join([id for id in texts]) if texts is not None else 'ALL'
    g.titles = ', '.join([engine.id2title[id] for id in texts]) if texts is not None else 'ALL'
    g.data = data
    g.id2title = engine.id2title
    g.to_percentage = lambda x : f"{x:.3%}"

    if data is None:
        flash("Bad query or language.")
    else:
        return render_template('search.html')
