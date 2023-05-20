import json
import sys
import requests
import logging
from flask import Flask, request, jsonify, make_response
from collections import OrderedDict
from pymongo import MongoClient

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

naor_api = 'DhpS7Wzw0QSQ3UlBWFYxHw==117Elk5BjCVfTjoM'

client = MongoClient("mongodb://mongo:27017/")
db = client["Cloud2_DB"]
dishes_collection = db["Dishes"]
meals_collection = db["Meals"]
diets_collection = db["Diets"]

# logger.info(f"combined_json: {combined_json}")

# Adding some object to the collections for testing purposes
# diets_collection.insert_one({"_id": 1, "name": "diet1"})
# meals_collection.insert_one({"_id": 1, "name": "meal1"})
# dishes_collection.insert_one({"_id": 1, "name": "dish1"})
# diets_collection.insert_one({"_id": 2, "name": "diet2"})
# meals_collection.insert_one({"_id": 2, "name": "meal2"})
# dishes_collection.insert_one({"_id": 2, "name": "dish2"})

# first time starting up this service as no document with _id ==0 exists
if dishes_collection.find_one({"_id": 0}) is None:
    # insert a document into the database to have one "_id" index that starts at 0 and a field named "cur_key"
    dishes_collection.insert_one({"_id": 0, "cur_key": 0})
    print("Inserted document containing cur_key with _id == 0 into the collection")
    sys.stdout.flush()
if meals_collection.find_one({"_id": 0}) is None:
    # insert a document into the database to have one "_id" index that starts at 0 and a field named "cur_key"
    meals_collection.insert_one({"_id": 0, "cur_key": 0})
    print("Inserted document containing cur_key with _id == 0 into the collection")
    sys.stdout.flush()
if diets_collection.find_one({"_id": 0}) is None:
    # insert a document into the database to have one "_id" index that starts at 0 and a field named "cur_key"
    diets_collection.insert_one({"_id": 0, "cur_key": 0})
    print("Inserted document containing cur_key with _id == 0 into the collection")
    sys.stdout.flush()

# Python list
dishes_list = [{}]
meals_list = [{}]
meals_dict = [{}]


def check_if_name_exists_in_dishes_db(name):
    doc = dishes_collection.find_one({"name": name})
    if doc is not None:
        print(name + " already exists in Mongo with key " +
              str(doc["_id"]))
        sys.stdout.flush()
        return True
    return False


def check_if_ninjas_recognize_name(dish_name):
    api_url = 'https://api.api-ninjas.com/v1/nutrition?query={}'.format(
        dish_name)
    response = requests.get(
        api_url, headers={'X-Api-Key': naor_api})
    json_dict = response.json()  # [{brisket},{fries}]
    if response.status_code == requests.codes.ok and len(json_dict) > 0:
        if len(json_dict) == 2:
            if "name" in json_dict[0] and "name" in json_dict[1] and json_dict[0]["name"] in dish_name and json_dict[1]["name"] in dish_name:
                return True
        elif "name" in json_dict[0] and json_dict[0]["name"] == dish_name:
            return True
    return False


def check_for_errors(data):
    # Request content-type is not application/json
    content_type = request.headers.get("Content-Type")
    if content_type != 'application/json':
        return make_response(jsonify(0), 415)

    # Name parameter was not specified
    if "name" not in data:
        output = make_response(jsonify(-1), 400)
        return output

    # That dish of given name already exists
    in_dishes_db = check_if_name_exists_in_dishes_db(data['name'])
    if in_dishes_db is True:
        output = make_response(jsonify(-2), 400)
        return output

    # API was not reachable, or some server error
    api_url = 'https://api.api-ninjas.com/v1/nutrition'
    response = requests.get(
        api_url, headers={'X-Api-Key': naor_api})
    if response.status_code // 100 != 2 and response.status_code // 100 != 3 and response.status_code // 100 != 4:
        return make_response(jsonify(-4), 400)

    # Ninjas API doesn't recognize dish name
    name_exists_in_ninjas_api = check_if_ninjas_recognize_name(data['name'])
    if name_exists_in_ninjas_api is False:
        output = make_response(jsonify(-3), 400)
        return output

    return None


@app.post('/dishes')
def add_dish():
    content_type = request.headers.get('Content-Type')
    if content_type != 'application/json':
        return make_response(jsonify(0), 415)

    data = request.get_json()
    response = check_for_errors(data)
    # "None" means no errors in the previous checks.
    if response is not None:
        return response

    dish_name = data['name']

    # doc = dishes_collection.find_one({"name": dish_name})
    # if doc is not None:
    #     print(dish_name + " already exists in Mongo with key " +
    #           str(doc["_id"]))
    #     sys.stdout.flush()
    #     return dish_name + " already exists in Mongo with key " + str(doc["_id"]), 404

    detailed_dish = {}
    api_url = 'https://api.api-ninjas.com/v1/nutrition?query={}'.format(
        dish_name)
    response = requests.get(api_url, headers={'X-Api-Key': naor_api})
    json_dict = response.json()
    # print(json_dict) For testing purposes
    if json_dict != {'message': 'Internal server error'} and 'message' not in json_dict and isinstance(json_dict, list):
        # doc containing cur_key has the value of 0 for its "_id" field
        docID = {"_id": 0}
        # retrieve the doc with "_id" value = 0 and extract the "cur_key" value from it and increment its value
        cur_key = dishes_collection.find_one(docID)["cur_key"] + 1
        # set the "cur_key" field of the doc that meets the docID constraint to the updated value cur_key
        result = dishes_collection.update_one(
            docID, {"$set": {"cur_key": cur_key}})

        if len(json_dict) == 2:
            detailed_dish = show_only_requested_json_keys_for_combined_dish(
                dish_name, json_dict[0], json_dict[1])
        elif len(json_dict) == 1:
            detailed_dish = show_only_requested_json_keys(
                json_dict[0])

        dishes_collection.insert_one(
            {"_id": cur_key, "name": detailed_dish["name"], "cal": detailed_dish["cal"], "size": detailed_dish["size"],
             "sodium": detailed_dish["sodium"], "sugar": detailed_dish["sugar"]})
        print("inserted the dish " + dish_name +
              " into mongo with ID " + str(cur_key))
        sys.stdout.flush()

        return make_response(jsonify(cur_key), 201)

    return make_response(jsonify(-4), 400)


@app.get('/dishes')
def get_json_all_dishes():
    cursor = dishes_collection.find({"_id": {"$gte": 1}})
    # !! need to check for error
    print("mongo retrieved all dishes")
    cursor_list = list(cursor)  # convert cursor object into list
    print("List of dishes:")
    for cursor in cursor_list:
        print(cursor["name"])
    sys.stdout.flush()
    # convert list to JSON array
    cursor_json = json.dumps(cursor_list, indent=4)
    return cursor_json, 200


@app.get('/dishes/<id_or_name>')
def get_specific_dish(id_or_name):
    if "0" <= str(id_or_name[0]) <= "9":
        return get_dish_by_id(id_or_name)
    else:
        return get_dish_by_name(id_or_name)


def get_dish_by_id(dish_id):
    dish_id = int(dish_id)
    docID = {"_id": 0}
    cur_key = dishes_collection.find_one(docID)["cur_key"]
    dish = dishes_collection.find_one({"_id": dish_id})
    if dish_id == 0 or dish_id > cur_key or dish is None:
        return make_response(jsonify(-5), 404)
    else:
        return json.dumps(dish, indent=4)


def get_dish_by_name(name):
    dish = dishes_collection.find_one({"name": name})
    if dish is None:
        return make_response(jsonify(-5), 404)
    else:
        return json.dumps(dish, indent=4)


@app.get('/dishes/')
def name_or_id_not_specified_get_dishes():
    return make_response(jsonify(-1), 400)


@app.delete('/dishes/')
def name_or_id_not_specified_delete_dishes():
    return make_response(jsonify(-1), 400)


@app.delete('/dishes/<id_or_name>')
def delete_specific_dish(id_or_name):
    if "0" <= str(id_or_name[0]) <= "9":
        return delete_dish_by_id(id_or_name)
    else:
        return delete_dish_by_name(id_or_name)


def delete_dish_by_id(dish_id):
    dish_id = int(dish_id)
    docID = {"_id": 0}
    cur_key = dishes_collection.find_one(docID)["cur_key"]
    dish = dishes_collection.find_one({"_id": dish_id})
    if dish_id == 0 or dish_id > cur_key or dish is None:
        return make_response(jsonify(-5), 404)
    else:
        dishes_collection.delete_one({"_id": dish_id})
        return jsonify(dish_id)


def delete_dish_by_name(dish_name):
    dish = dishes_collection.find_one({"name": dish_name})
    if dish is None:
        return make_response(jsonify(-5), 404)
    else:
        dish_id = dish["_id"]
        dishes_collection.delete_one({"name": dish_name})
        return jsonify(dish_id)


def get_dictionary_for_json(dish_index):
    api_url = 'https://api.api-ninjas.com/v1/nutrition?query={}'.format(
        dishes_list[dish_index])
    response = requests.get(
        api_url, headers={'X-Api-Key': naor_api})
    json_dict = response.json()
    return show_only_requested_json_keys(json_dict[0])


def show_only_requested_json_keys(original_dict):
    new_dict = OrderedDict()
    new_dict["name"] = original_dict["name"]
    new_dict["cal"] = original_dict["calories"]
    new_dict["size"] = original_dict["serving_size_g"]
    new_dict["sodium"] = original_dict["sodium_mg"]
    new_dict["sugar"] = original_dict["sugar_g"]
    return new_dict


def show_only_requested_json_keys_for_combined_dish(original_name, first_meal_dict, second_meal_dict):
    new_dict = OrderedDict()
    new_dict["name"] = original_name
    new_dict["cal"] = first_meal_dict["calories"] + \
        second_meal_dict["calories"]
    new_dict["size"] = first_meal_dict["serving_size_g"] + \
        second_meal_dict["serving_size_g"]
    new_dict["sodium"] = first_meal_dict["sodium_mg"] + \
        second_meal_dict["sodium_mg"]
    new_dict["sugar"] = first_meal_dict["sugar_g"] + \
        second_meal_dict["sugar_g"]
    return new_dict


# Meals


@app.post('/meals')
def add_meal():
    content_type = request.headers.get('Content-Type')
    if content_type != 'application/json':
        return make_response(jsonify(0), 415)

    data = request.get_json()
    response = check_for_errors_in_meals(data)

    if response is not None:
        return response

    meal_name = data['name']
    meal = create_specific_meal_dict(data)
    docID = {"_id": 0}
    cur_key = meals_collection.find_one(docID)["cur_key"] + 1
    meals_collection.update_one(docID, {"$set": {"cur_key": cur_key}})
    meals_collection.insert_one(
        {"_id": cur_key, "name": meal_name, "appetizer": meal.get("appetizer"), "main": meal.get("main"),
         "dessert": meal.get("dessert"), "cal": meal.get("cal"), "sodium": meal.get("sodium"), "sugar": meal.get("sugar")})
    print("inserted the meal " + meal_name +
          " into mongo with ID " + str(cur_key))
    sys.stdout.flush()

    return make_response(jsonify(cur_key), 201)


@app.get('/meals')
def get_json_all_meals():
    diet_name = request.args.get('diet')
    combined_json = {}

    if diet_name is None:
        for index, meal_name in enumerate(meals_list):
            if index != 0 and index <= len(meals_list) and meals_list[index] != {}:
                meal = meals_dict[int(index)]
                new_dict = create_specific_meal_dict(meal)
                if new_dict == {}:
                    return make_response(jsonify(-4), 400)
                elif new_dict:
                    combined_json[str(index)] = new_dict

    else:
        conform_meals_index = 0
        diets_arr = requests.get('http://localhost:8005/diets').json()

        for diet in diets_arr:
            if diet['diet']['name'] == diet_name:
                break

        for index, meal_name in enumerate(meals_list):
            if index != 0 and index <= len(meals_list) and meals_list[index] != {}:
                meal = meals_dict[int(index)]
                specific_meal = create_specific_meal_dict(meal)
                if specific_meal == {}:
                    return make_response(jsonify(-4), 400)
                elif check_if_conform_diet(diet['diet'], specific_meal):
                    combined_json[str(conform_meals_index)] = specific_meal
                    conform_meals_index += 1

    # logger.info(f"combined_json: {combined_json}")
    return json.dumps(combined_json, indent=4)


def check_for_errors_in_meals(data):
    content_type = request.headers.get("Content-Type")
    if content_type != 'application/json':
        return make_response(jsonify(0), 415)

    if "name" not in data or "appetizer" not in data or "main" not in data or "dessert" not in data:
        output = make_response(jsonify(-1), 400)
        return output

    name_exists_in_list = check_if_name_exists_in_meals_db(data['name'])
    if name_exists_in_list is True:
        output = make_response(jsonify(-2), 400)
        return output

    appetizer_id = int(data['appetizer'])
    main_id = int(data['main'])
    dessert_id = int(data['dessert'])

    if check_if_dish_in_db(appetizer_id) is False or check_if_dish_in_db(
            main_id) is False or check_if_dish_in_db(dessert_id) is False:
        return make_response(jsonify(-5), 404)

    return None


def check_if_dish_in_db(dish_id):
    dish_id = int(dish_id)
    docID = {"_id": 0}
    cur_key = dishes_collection.find_one(docID)["cur_key"]
    dish = dishes_collection.find_one({"_id": dish_id})
    if dish_id == 0 or dish_id > cur_key or dish is None:
        return False
    return True


def check_if_name_exists_in_meals_db(name):
    doc = meals_collection.find_one({"name": name})
    if doc is not None:
        print(name + " already exists in Mongo with key " +
              str(doc["_id"]))
        sys.stdout.flush()
        return True
    return False

# If one of the responses is 'Internal server error' return -1


# def get_sum(param, appetizer_id, main_id, dessert_id):
#     appetizer_param = dishes_collection.find_one({"_id": appetizer_id})[param]
#     main_param = dishes_collection.find_one({"_id": main_id})[param]
#     dessert_param = dishes_collection.find_one({"_id": dessert_id})[param]

#     return appetizer_param + main_param + dessert_param

def get_sum(param, appetizer_id, main_id, dessert_id):
    appetizer_doc = dishes_collection.find_one({"_id": appetizer_id})
    main_doc = dishes_collection.find_one({"_id": main_id})
    dessert_doc = dishes_collection.find_one({"_id": dessert_id})

    if not appetizer_doc or not main_doc or not dessert_doc:
        return -1

    appetizer_param = appetizer_doc.get(param)
    main_param = main_doc.get(param)
    dessert_param = dessert_doc.get(param)

    if appetizer_param is None or main_param is None or dessert_param is None:
        return -1

    return appetizer_param + main_param + dessert_param


@app.get('/meals/<id_or_name>')
def get_specific_meal(id_or_name):
    if "0" <= str(id_or_name[0]) <= "9":
        return get_meal_by_id(id_or_name)
    else:
        return get_meal_by_name(id_or_name)


def get_meal_by_id(meal_id):
    meal_id = int(meal_id)
    if meal_id == 0 or meal_id >= len(meals_list) or meals_list[meal_id] == {}:
        return make_response(jsonify(-5), 404)
    else:
        meal = meals_dict[int(meal_id)]
        new_dict = create_specific_meal_dict(meal)
        if new_dict:
            dict_for_json = new_dict

        return json.dumps(dict_for_json, indent=4)


def get_meal_by_name(name):
    try:
        meal_id = meals_list.index(name)
        meal = meals_dict[int(meal_id)]
        new_dict = create_specific_meal_dict(meal)
        if new_dict:
            dict_for_json = new_dict
        return json.dumps(dict_for_json, indent=4)

    except ValueError:
        return make_response(jsonify(-5), 404)

# If one of the get_sum value is -1 return an empty list


def create_specific_meal_dict(meal):
    appetizer_id = int(meal["appetizer"])
    main_id = int(meal["main"])
    dessert_id = int(meal["dessert"])
    cal_sum = get_sum("cal", appetizer_id, main_id, dessert_id)
    sodium_sum = get_sum("sodium", appetizer_id, main_id, dessert_id)
    sugar_sum = get_sum("sugar", appetizer_id, main_id, dessert_id)
    new_dict = OrderedDict()

    if cal_sum == -1 or sodium_sum == -1 or sugar_sum == -1:
        return new_dict

    new_dict["name"] = meal["name"]
    new_dict["appetizer"] = int(appetizer_id)
    new_dict["main"] = int(main_id)
    new_dict["dessert"] = int(dessert_id)
    new_dict["cal"] = float(cal_sum)
    new_dict["sodium"] = float(sodium_sum)
    new_dict["sugar"] = float(sugar_sum)

    return new_dict


def check_if_conform_diet(diet, meal):
    if float(meal['cal']) <= float(diet['cal']) and float(meal['sodium']) <= float(diet['sodium']) and float(meal['sugar']) <= float(diet['sugar']):
        return True
    else:
        return False


@app.delete('/meals/<id_or_name>')
def delete_specific_meal(id_or_name):
    if "0" <= str(id_or_name[0]) <= "9":
        return delete_meal_by_id(id_or_name)
    else:
        return delete_meal_by_name(id_or_name)


def delete_meal_by_id(meal_id):
    meal_id = int(meal_id)
    if meal_id == 0 or meal_id >= len(meals_list) or meals_list[meal_id] == {}:
        return make_response(jsonify(-5), 404)
    else:
        meals_list[meal_id] = {}
        meals_dict[meal_id] = {}
        return jsonify(meal_id)


def delete_meal_by_name(meal_name):
    try:
        index_of_meal = meals_list.index(meal_name)
        meals_list[index_of_meal] = {}
        meals_dict[index_of_meal] = {}
        return jsonify(index_of_meal)
    except ValueError:
        return make_response(jsonify(-5), 404)


@app.get('/meals/')
def name_or_id_not_specified_get_meals():
    return make_response(jsonify(-1), 400)


@app.delete('/meals/')
def name_or_id_not_specified_delete_meals():
    return make_response(jsonify(-1), 400)


@app.put('/meals/<meal_id>')
def put_meal_new_details(meal_id):
    if "0" <= str(meal_id[0]) <= "9" and len(meals_list) > int(meal_id) and meals_list[int(meal_id)] != {}:
        meal_id = int(meal_id)
        content_type = request.headers.get('Content-Type')
        if content_type != 'application/json':
            return make_response(jsonify(0), 415)

        data = request.get_json()
        response = check_for_errors_in_meals(data)
        if response is not None:
            return response

        change_meal(meal_id, data)

        return make_response(jsonify(meal_id), 200)
    else:
        return make_response(jsonify(-1), 400)


def change_meal(meal_id, new_meal):
    meals_list[meal_id] = new_meal['name']
    meals_dict[meal_id]["name"] = new_meal['name']
    meals_dict[meal_id]["appetizer"] = new_meal['appetizer']
    meals_dict[meal_id]["main"] = new_meal['main']
    meals_dict[meal_id]["dessert"] = new_meal['dessert']


app.run(host="localhost", port=5001, debug=True, use_reloader=False)
