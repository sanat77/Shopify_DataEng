from functools import total_ordering
import time
import requests
import json
import datetime
import pymongo
from flask import Flask, render_template
from pymongo import MongoClient

app = Flask(__name__)


def GetMongoDBConnection():
    try:
        client = MongoClient('mongodb+srv://shopify:shopify123@shopifycluster.1ku6j.mongodb.net/data?retryWrites=true&w=majority')
        client.server_info()
        print("connected")
    except pymongo.errors.ServerSelectionTimeoutError as err:
        print(f"couldn't connect {err}")

    try:
        db = client['data']
        print("collection found")
    except NameError:
        print("no collection")

    return db

def initializeDB():
    deleteAll()
    collection = GetMongoDBConnection()['db']
    price = GetMongoDBConnection()['running_price']
    products = [{'_id': '1', 'name': 'Belt', 'price': '100', 'image': 'images/belt.jpeg', 'inventory': '10'},
                {'_id': '2', 'name': 'Coat', 'price': '750', 'image': 'images/coat.jpeg', 'inventory': '0'},
                {'_id': '3', 'name': 'Pant', 'price': '200', 'image': 'images/pant.jpeg', 'inventory': '70'},
                {'_id': '4', 'name': 'Shirt', 'price': '250', 'image': 'images/shirt.jpeg', 'inventory': '5'},
                {'_id': '5', 'name': 'Shoes', 'price': '300', 'image': 'images/shoes.jpeg', 'inventory': '1'}]
    collection.insert_many(products)
    price.insert_one({"price":"0"})


def deleteAll():
    GetMongoDBConnection()['db'].delete_many({})
    GetMongoDBConnection()['running_price'].delete_many({})


@app.route("/")
def home():
    collection = GetMongoDBConnection()['db']
    price_collection = GetMongoDBConnection()['running_price']
    items = collection.find({})
    products = []
    for item in items:
        product = {
            "_id": item['_id'],
            "name": item['name'],
            "price": item['price'],
            "src": item['image'],
            "inventory": item['inventory']
        }
        products.append(product)
    
    total_paid = price_collection.find_one({})["price"]
    return render_template('index.html', products=products, total_paid=total_paid)


@app.route("/reset")
def reset_page():
    deleteAll()
    initializeDB()
    return render_template("render_message.html", message="Reset Successful!!")


@app.route("/buy/<item_id>")
def buy(item_id):
    collection = GetMongoDBConnection()['db']
    total_paid_collection = GetMongoDBConnection()['running_price']
    running_price = int(total_paid_collection.find_one({})['price'])
    item = collection.find_one({"_id": item_id})
    item_name = item["name"]
    item_price = int(item["price"])
    item_count = int(item["inventory"])

    if (item_count <= 0):
        return render_template("render_message.html", message=f"YEET!!! Cannot purchase {item_name}, Insufficient Stock :(")

    collection.find_one_and_update({"_id": item_id}, {'$set': {"inventory": item_count-1}})

    total_paid_collection.find_one_and_update({}, {'$set': {"price": running_price + item_price}})

    return render_template("render_message.html", message=f"{item_name} Purchase Successful!!")

if __name__ == '__main__':
    initializeDB()
    app.run(host="localhost", port=3000, debug=True)