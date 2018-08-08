from flask import Flask

from config import DevelopmentConfig

from models import db
from models import User

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)

@app.route('/')
def index():
    return "Bot Prendido"

if __name__=='__main__':
    db.init_app(app)

    with app.app_context():
        db.create_all()

    app.run(port=8000)
