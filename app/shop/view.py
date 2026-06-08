from flask import Blueprint, render_template

app_shop = Blueprint('shop', __name__, template_folder='../templates')


@app_shop.route('/', defaults={'path': ''})
@app_shop.route('/<path:path>')
def index(path):
    return render_template('shop/index.html')
