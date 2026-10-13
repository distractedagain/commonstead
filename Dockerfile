# Optional local container. No Python packages or frontend build are needed.
# This base-image tag is mutable; record/pin a reviewed digest for deployment.
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN groupadd --gid 10001 commonstead && useradd --uid 10001 --gid 10001 --no-create-home commonstead \
    && mkdir /data && chown 10001:10001 /data
COPY --chown=10001:10001 commonstead /app/commonstead
USER 10001:10001
EXPOSE 8765
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/health', timeout=2).read()"
CMD ["python", "-m", "commonstead", "--host", "0.0.0.0", "--port", "8765", "--db", "/data/commonstead.sqlite3"]
