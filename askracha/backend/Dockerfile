# Use Python 3.10 slim base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install -r requirements.txt

# Copy application code
COPY . .

# Create persistent_index directory
RUN mkdir -p persistent_index

# Expose port 5000
EXPOSE 5000

# Set environment variables
ENV FLASK_ENV=development

# Run the application
CMD ["python", "-u", "app.py"]