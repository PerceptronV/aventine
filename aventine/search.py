from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from aventine.db import get_db

bp = Blueprint('search', __name__)

@bp.route('/')
def index():
    return "AVENTINE is awake."
