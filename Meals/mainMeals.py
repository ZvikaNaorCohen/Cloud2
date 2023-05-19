import json
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
diets_collection.insert_one({"_id": 1, "name": "diet1"})
meals_collection.insert_one({"_id": 1, "name": "meal1"})
dishes_collection.insert_one({"_id": 1, "name": "dish1"})

diets_collection.insert_one({"_id": 2, "name": "diet2"})
meals_collection.insert_one({"_id": 2, "name": "meal2"})
dishes_collection.insert_one({"_id": 2, "name": "dish2"})

# Python list
dishes_list = [{}]
meals_list = [{}]
meals_dict = [{}]


def check_if_name_exists_in_list(name): # May not be needed
    if name in dishes_list:
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
    name_exists_in_list = check_if_name_exists_in_list(data['name'])
    if name_exists_in_list is True:
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
    dishes_list.append(dish_name)
    index = dishes_list.index(dish_name)

    return make_response(jsonify(index), 201)


@app.get('/dishes')
def get_json_all_dishes():
    combined_json = {}
    for index, dish_name in enumerate(dishes_list):
        if index > 0:
            api_url = 'https://api.api-ninjas.com/v1/nutrition?query={}'.format(
                dish_name)
            response = requests.get(
                api_url, headers={'X-Api-Key': naor_api})
            json_dict = response.json()
            print(json_dict)
            if json_dict != {'message': 'Internal server error'} and 'message' not in json_dict and isinstance(json_dict, list):
                if len(json_dict) == 2:
                    combined_json[str(index)] = show_only_requested_json_keys_for_combined_dish(
                        dish_name, json_dict[0], json_dict[1])
                elif len(json_dict) == 1:
                    combined_json[str(index)] = show_only_requested_json_keys(
                        json_dict[0])
            else:
                return make_response(jsonify(-4), 400)

    return json.dumps(combined_json, indent=4)


@app.get('/dishes/<id_or_name>')
def get_specific_dish(id_or_name):
    if "0" <= str(id_or_name[0]) <= "9":
        return get_dish_by_id(id_or_name)
    else:
        return get_dish_by_name(id_or_name)


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
    if dish_id == 0 or dish_id >= len(dishes_list) or dishes_list[dish_id] == {}:
        return make_response(jsonify(-5), 404)
    else:
        # del dishes_list[dish_id]
        dishes_list[dish_id] = {}
        return jsonify(dish_id)


def delete_dish_by_name(dish_name):
    try:
        index_of_dish = dishes_list.index(dish_name)
        # del dishes_list[index_of_dish]
        dishes_list[index_of_dish] = {}
        return jsonify(index_of_dish)
    except ValueError:
        return make_response(jsonify(-5), 404)


def get_dish_by_id(dish_id):
    dish_id = int(dish_id)
    if dish_id == 0 or dish_id >= len(dishes_list) or dishes_list[dish_id] == {}:
        return make_response(jsonify(-5), 404)
    else:
        dict_for_json = get_dictionary_for_json(dish_id)
        return json.dumps(dict_for_json, indent=4)


def get_dish_by_name(name):
    try:
        index_of_dish = dishes_list.index(name)
        dict_for_json = get_dictionary_for_json(index_of_dish)
        return json.dumps(dict_for_json, indent=4)
    except ValueError:
        return make_response(jsonify(-5), 404)


def get_dictionary_for_json(dish_index):
    api_url = 'https://api.api-ninjas.com/v1/nutrition?query={}'.format(
        dishes_list[dish_index])
    response = requests.get(
        api_url, headers={'X-Api-Key': naor_api})
    json_dict = response.json()
    return show_only_requested_json_keys(json_dict[0])


def show_only_requested_json_keys(original_dict):
    new_dict = OrderedDict()
    index_of_dish = dishes_list.index(original_dict["name"])
    new_dict["name"] = original_dict["name"]
    new_dict["ID"] = index_of_dish
    new_dict["cal"] = original_dict["calories"]
    new_dict["size"] = original_dict["serving_size_g"]
    new_dict["sodium"] = original_dict["sodium_mg"]
    new_dict["sugar"] = original_dict["sugar_g"]

    return new_dict


def show_only_requested_json_keys_for_combined_dish(original_name, first_meal_dict, second_meal_dict):
    new_dict = OrderedDict()
    index_of_dish = dishes_list.index(original_name)
    new_dict["name"] = original_name
    new_dict["ID"] = index_of_dish
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
    meals_list.append(meal_name)
    index = meals_list.index(meal_name)
    meals_dict.append(data)
    return make_response(jsonify(index), 201)


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

    name_exists_in_list = check_if_name_exists_in_meals_list(data['name'])
    if name_exists_in_list is True:
        output = make_response(jsonify(-2), 400)
        return output

    appetizer_id = int(data['appetizer'])
    main_id = int(data['main'])
    dessert_id = int(data['dessert'])

    if check_if_dish_in_list_by_id(appetizer_id) is False or check_if_dish_in_list_by_id(
            main_id) is False or check_if_dish_in_list_by_id(dessert_id) is False:
        return make_response(jsonify(-5), 404)

    appetizer = dishes_list[int(appetizer_id)]
    main = dishes_list[int(main_id)]
    dessert = dishes_list[int(dessert_id)]

    if check_if_name_exists_in_list(appetizer) and check_if_name_exists_in_list(main) and check_if_name_exists_in_list(
            dessert):
        return None
    else:
        return make_response(jsonify(-5), 404)


def check_if_dish_in_list_by_id(dish_id):
    dish_id = int(dish_id)
    if dish_id == 0 or dish_id >= len(dishes_list) or dishes_list[dish_id] == {}:
        return False
    return True


def check_if_name_exists_in_meals_list(name):
    if name in meals_list:
        return True
    return False

# If one of the responses is 'Internal server error' return -1


def get_sum(param, appetizer_id, main_id, dessert_id):
    api_url = 'https://api.api-ninjas.com/v1/nutrition?query={}'.format(
        dishes_list[int(appetizer_id)])
    appetizer_response = requests.get(
        api_url, headers={'X-Api-Key': naor_api})
    appetizer_json_dict = appetizer_response.json()

    if appetizer_json_dict == {'message': 'Internal server error'}:
        return -1

    appetizer_param = appetizer_json_dict[0][param]

    api_url = 'https://api.api-ninjas.com/v1/nutrition?query={}'.format(
        dishes_list[int(main_id)])
    main_response = requests.get(
        api_url, headers={'X-Api-Key': naor_api})
    main_json_dict = main_response.json()

    if main_json_dict == {'message': 'Internal server error'}:
        return -1

    main_param = main_json_dict[0][param]

    api_url = 'https://api.api-ninjas.com/v1/nutrition?query={}'.format(
        dishes_list[int(dessert_id)])
    dessert_response = requests.get(
        api_url, headers={'X-Api-Key': naor_api})
    dessert_json_dict = dessert_response.json()

    if dessert_json_dict == {'message': 'Internal server error'}:
        return -1

    dessert_param = dessert_json_dict[0][param]

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
    appetizer_id = meal["appetizer"]
    main_id = meal["main"]
    dessert_id = meal["dessert"]

    cal_sum = get_sum("calories", appetizer_id, main_id, dessert_id)
    sodium_sum = get_sum("sodium_mg", appetizer_id, main_id, dessert_id)
    sugar_sum = get_sum("sugar_g", appetizer_id, main_id, dessert_id)

    new_dict = OrderedDict()

    if cal_sum == -1 or sodium_sum == -1 or sugar_sum == -1:
        return new_dict

    index_of_dish = meals_list.index(meal["name"])
    new_dict["name"] = meal["name"]
    new_dict["ID"] = index_of_dish
    new_dict["appetizer"] = appetizer_id
    new_dict["main"] = main_id
    new_dict["dessert"] = dessert_id
    new_dict["cal"] = cal_sum
    new_dict["sodium"] = sodium_sum
    new_dict["sugar"] = sugar_sum

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
