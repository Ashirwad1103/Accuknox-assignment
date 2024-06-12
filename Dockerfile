# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

RUN python socialnetworking/manage.py makemigrations
RUN python socialnetworking/manage.py migrate

# Expose port 8000
EXPOSE 8000

# Command to run Django server
CMD ["python", "socialnetworking/manage.py", "runserver", "0.0.0.0:8000"]
