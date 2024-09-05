# Base image with CUDA support
FROM nvidia/cuda:12.2.0-base-ubuntu22.04

# Install curl, Python, pip, and other dependencies
RUN apt-get update && apt-get install -y \
    curl \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Set the working directory
WORKDIR /app

# Install required Python packages
RUN pip3 install Flask Flask-CORS httpx

# Copy init_ollama script
COPY . .
RUN chmod +x ./init_ollama.sh

# Run the init_ollama script during the build
RUN ./init_ollama.sh

# Set the environment variable for ollama
ENV OLLAMA_HOST=0.0.0.0:11434

WORKDIR /app/src

# Expose the port for Ollama and Flask
EXPOSE 11434
EXPOSE 11435


# Replace CMD to start Flask application (instead of ollama directly)
CMD ["python3", "server.py"]
