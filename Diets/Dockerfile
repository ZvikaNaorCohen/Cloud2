FROM python:alpine3.17
WORKDIR /Cloud2/Diets
COPY mainDiets.py .
RUN pip install flask
RUN pip install flask_restful
RUN pip install jsonify
RUN pip install make_response
RUN pip install pymongo
EXPOSE 5002
ENV FLASK_APP=mainDiets.py
ENV FLASK_RUN_PORT=5002
CMD ["python3", "-m", "flask", "run", "--host=0.0.0.0"]