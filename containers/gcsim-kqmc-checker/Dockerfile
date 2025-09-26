FROM python:3
RUN mkdir /usr/src/app
WORKDIR /usr/src/app
COPY ./requirements.txt .
RUN pip3 install -r requirements.txt
COPY *.py /usr/src/app/
RUN ls -l /usr/src/app/
RUN if [ ! -f /usr/src/app/KQMCCheckerDiscordBot.py ]; then echo "Python script not found"; exit 1; fi
ENTRYPOINT ["python3", "/usr/src/app/KQMCCheckerDiscordBot.py"]
