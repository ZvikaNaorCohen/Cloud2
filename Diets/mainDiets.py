from flask import Flask, request, jsonify, make_response
from pymongo import MongoClient
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
        return make_response(jsonify("POST expects content type to be application/json"), 415)

    diet = request.get_json()

    response = check_for_errors(diet)
    if response is not None:
        return response

    diet_name = diet["name"]
    docID = {"_id": 0}
    cur_key = diets_collection.find_one(docID)["cur_key"] + 1
    diets_collection.update_one(docID, {"$set": {"cur_key": cur_key}})
    diets_collection.insert_one(
        {"_id": cur_key, "name": diet_name, "cal": diet["cal"], "sodium": diet["sodium"], "sugar": diet["sugar"]})
    print("inserted the dish " + diet_name +
          " into mongo with ID " + str(cur_key))
    sys.stdout.flush()

    return make_response(jsonify("Diet " + diet_name + " was created successfully"), 201)


@app.get('/diets')
def get_diets():
    cursor = diets_collection.find({"_id": {"$gte": 1}})
    print("mongo retrieved all diets")
    cursor_list = list(cursor)
    print("List of diets:")
    for cursor in cursor_list:
        print(cursor["name"])
    sys.stdout.flush()

    # Remove the _id field from each document
    for diet in cursor_list:
        diet.pop('_id', None)

    cursor_json = json.dumps(cursor_list, indent=4)
    return cursor_json, 200


@app.get('/diets/<diet_name>')
def get_specific_diet(diet_name):
    diet = diets_collection.find_one({"name": diet_name})
    if diet is None:
        return make_response(jsonify("Diet " + diet_name + " not found"), 404)
    else:
        return json.dumps(diet, indent=4)


def check_for_errors(diet):
    # One of parameters was not specified
    if "name" not in diet or "cal" not in diet or "sodium" not in diet or "sugar" not in diet:
        return make_response(jsonify("Incorrect POST format"), 422)

    # That diet of given name already exists
    if check_if_diet_exists_in_db(diet["name"]) is True:
        return make_response(jsonify("Diet with " + diet["name"] + " already exists"), 422)

    return None


def check_if_diet_exists_in_db(diet_name):
    if diets_collection.find_one({"name": diet_name}) is None:
        return False
    return True


app.run(host="localhost", port=5002, debug=True, use_reloader=False)
