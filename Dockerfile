# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.8-slim-buster

EXPOSE 5000

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Upgrading pip
RUN python -m pip install -U pip

# Install pip requirements
COPY requirements.txt .
RUN python -m pip install -r requirements.txt

# Set up environment value
COPY set_env.sh .
RUN chmod +x set_env.sh
RUN ./set_env.sh
ENV SYSTEM_STORAGE_NAME=imagerecogtestsys
ENV SYSTEM_STORAGE_KEY="SjIKAqbNWm4uHUOHxHNB3K9RaNVNC7qAQpg7cHRLGMMMZQf2m/xhaVBpnZXSr4JgmWliBdmRmf9M9vvC+FLTzQ=="
ENV AZURE_INSIGHT_CONNECTION="InstrumentationKey=88fbe81d-3718-489e-9779-d402eebf1a90;IngestionEndpoint=https://japaneast-1.in.applicationinsights.azure.com/"

WORKDIR /app
COPY . /app

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
