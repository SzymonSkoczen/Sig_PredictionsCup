FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir .
# .env and data/ (market map, database) are mounted at runtime, never baked into the image
VOLUME ["/app/data"]
HEALTHCHECK --interval=2m --timeout=10s \
  CMD python -c "import time,sys; sys.exit(time.time()-int(open('/app/data/heartbeat').read())>600)"
ENTRYPOINT ["sigcup"]
CMD ["run"]
