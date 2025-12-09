# Dockerfile for Puzzle Arcade Server

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install UV
RUN pip install uv

# Copy project files
COPY pyproject.toml ./
COPY config.yaml ./
COPY src/ ./src/

# Install dependencies
RUN uv pip install --system -e .
RUN uv pip install --system chuk-protocol-server

# Expose ports
# 8023 - Telnet
# 8024 - TCP
# 8025 - WebSocket
# 8026 - WebSocket-Telnet
EXPOSE 8023 8024 8025 8026

# Run the server using chuk-protocol-server launcher
CMD ["python", "-m", "chuk_protocol_server.server_launcher", "-c", "config.yaml"]
