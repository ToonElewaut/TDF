# Use an official Python runtime as a parent image
FROM python:3.11.8-slim

# Set the working directory in the container
WORKDIR /src

# Copy the current directory contents into the container at /app
COPY ./src /src

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Make port 8050 available to the world outside this container
EXPOSE 8050

# Define environment variable
ENV NAME World

# Run app.py when the container launches
CMD ["python", "app.py"]
