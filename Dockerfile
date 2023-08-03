# Use an official Python runtime as the base image
FROM python:3.8.10

# Set environment variables
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# Set the working directory in the container
WORKDIR /code

# Copy the project requirements to the working directory
COPY requirements.txt /code/

# Install development packages and MariaDB Connector/C
RUN apt-get update && apt-get install -y python3-dev build-essential libffi-dev default-libmysqlclient-dev

# Install project dependencies
RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project code to the working directory
COPY . /code/

## Run database migrations
#RUN python manage.py migrate

# Expose the port that the Django app will run on
EXPOSE 8000

# Set the default command to run the Django development server
#CMD python manage.py runserver 0.0.0.0:8000
CMD ["python", "app.py"]
