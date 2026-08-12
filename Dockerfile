# nv-sagegrouse -- reproducible environment for the full analysis pipeline.
# Build:  docker build -t nv-sagegrouse .
# Run:    docker run --rm -v $(pwd):/work nv-sagegrouse make v4
FROM ghcr.io/osgeo/gdal:ubuntu-full-3.9.2

RUN apt-get update && apt-get install -y --no-install-recommends \
      r-base r-base-dev grass-core curl ca-certificates make unzip \
    && rm -rf /var/lib/apt/lists/*

# uv (runs every Python pipeline script with its inline dependencies)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# DuckDB CLI
RUN curl -LsSf https://install.duckdb.org | sh
ENV PATH="/root/.duckdb/cli/latest:${PATH}"

# R model dependency (base R + MuMIn is the entire statistical footprint)
RUN Rscript -e 'install.packages("MuMIn", repos="https://cloud.r-project.org")'

WORKDIR /work
CMD ["make", "help"]
