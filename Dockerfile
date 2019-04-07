FROM python:3.7-slim-stretch

RUN pip install pipenv

COPY baseballclerk/*.py /usr/src/baseballclerk/baseballclerk/
COPY Pipfile Pipfile.lock setup.py /usr/src/baseballclerk/

WORKDIR /usr/src/baseballclerk

RUN pipenv install --system --deploy

WORKDIR /baseballclerk/

ENTRYPOINT [ "python", "-m", "baseballclerk" ]
CMD [ "-h" ]
