from flask_sqlalchemy import SQLAlchemy
import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(40))
    password = db.Column(db.String(66))
    createdAt = db.Column(db.DateTime(timezone=True), default="")
    updatedAt = db.Column(db.DateTime(timezone=True), default="")
