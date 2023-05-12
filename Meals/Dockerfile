FROM python:alpine3.17
# This Dockerfile.setport is for use with main.py
WORKDIR /Cloud1
COPY main.py .
RUN pip install flask
RUN pip install flask_restful
RUN pip install requests
RUN pip install jsonify
RUN pip install make_response
RUN pip install OrderedDict
EXPOSE 8000
ENV FLASK_APP=main.py
ENV FLASK_RUN_PORT=8000
CMD ["python3", "-m", "flask", "run", "--host=0.0.0.0"]