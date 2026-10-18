from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class ApiKey(db.Model):
    __tablename__ = "api_keys"
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), unique=True)
    quota = db.Column(db.Integer, default=1000)
    used = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Shot(db.Model):
    __tablename__ = "shots"
    id = db.Column(db.Integer, primary_key=True)
    key_id = db.Column(db.Integer, db.ForeignKey("api_keys.id"))
    url = db.Column(db.String(512), default="")
    format = db.Column(db.String(8), default="png")
    size = db.Column(db.Integer, default=0)
    cached = db.Column(db.Integer, default=0)
    at = db.Column(db.DateTime, default=datetime.utcnow)
