from flask import Flask, request, jsonify, make_response
from collections import OrderedDict
from pymongo import MongoClient
import requests
import json
import sys

app = Flask(__name__)

naor_api = 'DhpS7Wzw0QSQ3UlBWFYxHw==117Elk5BjCVfTjoM'

client = MongoClient("mongodb://mongo:27017/")
db = client["Cloud2_DB"]
diets_collection = db["Diets"]
if diets_collection.find_one({"_id": 0}) is None:
    # insert a document into the database to have one "_id" index that starts at 0 and a field named "cur_key"
    diets_collection.insert_one({"_id": 0, "cur_key": 0})
    print("Inserted document containing cur_key with _id == 0 into the collection")
    sys.stdout.flush()


@app.post('/diets')
def add_diet():
    content_type = request.headers.get('Content-Type')
    if content_type != 'application/json':
        return make_response(jsonify(0), 415)

    data = request.get_json()
    docID = {"_id": 0}
    cur_key = diets_collection.find_one(docID)["cur_key"] + 1
    diets_collection.update_one(docID, {"$set": {"cur_key": cur_key}})
    diets_collection.insert_one(
        {"_id": cur_key, "name": data["name"], "cal": data["cal"], "sodium": data["sodium"], "sugar": data["sugar"]})
    print("inserted the dish " + data["name"] +
          " into mongo with ID " + str(cur_key))
    sys.stdout.flush()

    return make_response(jsonify(cur_key), 201)


@app.get('/diets')
def get_diets():
    cursor = diets_collection.find({"_id": {"$gte": 1}})
    print("mongo retrieved all diets")
    cursor_list = list(cursor)
    print("List of diets:")
    for cursor in cursor_list:
        print(cursor["name"])
    sys.stdout.flush()
    cursor_json = json.dumps(cursor_list, indent=4)
    return cursor_json, 200


@app.get('/diets/<diet_name>')
def get_specific_diet(diet_name):
    diet = diets_collection.find_one({"name": diet_name})
    if diet is None:
        return make_response(jsonify(-5), 404)
    else:
        return json.dumps(diet, indent=4)


app.run(host="localhost", port=5002, debug=True, use_reloader=False)
