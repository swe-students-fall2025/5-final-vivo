FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Keep the project as a package (webapp) to match imports used in code/tests
COPY . /app/webapp

ENV FLASK_APP=webapp.app
ENV PYTHONPATH=/app
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

EXPOSE 5000

CMD ["flask", "run"]
