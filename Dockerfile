FROM python:3.7-slim-stretch

RUN pip install pipenv

COPY baseballclerk/*.py /src/baseballclerk/
COPY Pipfile Pipfile.lock setup.py /src/

WORKDIR /src/

RUN pipenv install --system --deploy

WORKDIR /baseballclerk/

ENTRYPOINT [ "python", "/src/baseballclerk/main.py" ]
CMD [ "-h" ]
