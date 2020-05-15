from flask import Flask

app = Flask(__name__)
app.config['SECRET_KEY'] = '878436c0a462c4145fa59eec2c43a66a'

#Import Blueprint routes objects
from onewebaccess.home.routes import blue

#Register Blueprint
app.register_blueprint(home.routes.blue)