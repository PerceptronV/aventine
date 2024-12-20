from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from aventine.library.engines import default_engine as engine

bp = Blueprint('home', __name__)

@bp.route('/')
def index():
    g.id2title = engine.id2title
    return render_template('home.html')
