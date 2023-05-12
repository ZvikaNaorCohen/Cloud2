from flask import Flask, request, jsonify, make_response
from collections import OrderedDict
import requests
import json

app = Flask(__name__)

naor_api = 'DhpS7Wzw0QSQ3UlBWFYxHw==117Elk5BjCVfTjoM'

diets_json_arr = []

def insert_to_diets_arr(dish):
    diets_json_arr.append(dish)

def return_diets_arr():
    result = []
    for i, dish in enumerate(diets_json_arr):
        result.append({"_id": i, "diet": dish})
    return json.dumps(result)

@app.post('/diets')
def add_diet():
    content_type = request.headers.get('Content-Type')
    if content_type != 'application/json':
        return make_response(jsonify(0), 415)

    data = request.get_json()
    insert_to_diets_arr(data)
    index = diets_json_arr.index(data)
    return make_response(jsonify(index), 201)

@app.route('/diets', methods=['GET'])
def get_diets():
    return make_response(return_diets_arr(), 200)


app.run(host="localhost", port=8005, debug=True)
