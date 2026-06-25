from flask import Blueprint, render_template
from flask_login import current_user

from controllers.auth import redirect_user_by_role

main = Blueprint('main', __name__)


@main.route('/')
def landing():
    if current_user.is_authenticated:
        return redirect_user_by_role(current_user)

    return render_template('landing_page.html')