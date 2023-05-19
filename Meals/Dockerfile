FROM python:alpine3.17
WORKDIR /Cloud2/Meals
COPY mainMeals.py .
RUN pip install flask
RUN pip install flask_restful
RUN pip install requests
RUN pip install jsonify
RUN pip install make_response
RUN pip install OrderedDict
RUN pip install pymongo
EXPOSE 5001
ENV FLASK_APP=mainMeals.py
ENV FLASK_RUN_PORT=5001
CMD ["python3", "-m", "flask", "run", "--host=0.0.0.0"]