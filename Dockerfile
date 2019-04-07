FROM python:3.7-slim-stretch

RUN pip install pipenv

WORKDIR /usr/local/src/baseballclerk

COPY baseballclerk/*.py ./baseballclerk/
COPY Pipfile Pipfile.lock setup.py ./

RUN pipenv install --system --deploy

WORKDIR /baseballclerk/

ENTRYPOINT [ "python", "-m", "baseballclerk" ]
CMD [ "-h" ]
