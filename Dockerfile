FROM python:3.11-alpine
WORKDIR /app
RUN pip install --no-cache-dir requests
COPY app.py .
EXPOSE 8080
CMD ["python", "app.py"]
