from app import db

class Products(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250))
    price = db.Column(db.String(50))

    def __init__(self, name, price):
        self.name = name
        self.price = price

class Deals(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    deal_type = db.Column(db.String(100), unique=True)
    deal_items = db.Column(db.String)

    def __init__(self, deal_type, deal_items):
        self.deal_type = deal_type
        self.deal_items = deal_items

    def __repr__(self):
        return f'{self.deal_type}'