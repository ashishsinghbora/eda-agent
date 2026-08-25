# ==============================================================================
# EDA-Agent Production Container Image
# Ubuntu 24.04 LTS with Open-Source EDA Suite (Verilator, Icarus Verilog, Yosys)
# ==============================================================================

FROM ubuntu:24.04 AS base

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    COCOTB_IGNORE_PYTHON_REQUIRES=1 \
    PATH="/home/edauser/.local/bin:$PATH"

# Install system dependencies, C/C++ compiler, Make, and open-source EDA tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    clang \
    git \
    make \
    pkg-config \
    libfl-dev \
    zlib1g-dev \
    iverilog \
    verilator \
    yosys \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    curl \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create dedicated non-root EDA user
RUN useradd -m -s /bin/bash -u 1000 edauser && \
    mkdir -p /workspace /home/edauser/.eda-agent && \
    chown -R edauser:edauser /workspace /home/edauser

# Switch to non-root user
USER edauser
WORKDIR /workspace

# Set up Python virtual environment in user directory
ENV VIRTUAL_ENV=/home/edauser/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install Python dependencies
COPY --chown=edauser:edauser requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# Copy source repository and install EDA-Agent in editable mode
COPY --chown=edauser:edauser . /workspace
RUN pip install --no-cache-dir -e .

# Expose FastAPI Web UI / WebSocket port
EXPOSE 8000

# Volume mount point for external RTL projects
VOLUME ["/workspace"]

# Default entrypoint: EDA-Agent CLI
ENTRYPOINT ["eda-agent"]
CMD ["--help"]
