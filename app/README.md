# Movie Review Aggregator

### How to run with Docker

1. Go into the app directory:

   ```sh
   cd app
   ```

2. Create a file named `.env` following the format in `.env.template` file:

   ```xml
   POSTGRES_USER=<your_postgres_user>
   POSTGRES_HOST=<your_postgres_host>
   POSTGRES_PASSWORD=<your_postgres_password>
   POSTGRES_DATABASE=<your_postgres_database_name>
   DB_PORT=<your_postgres_port>

   CRAWLER_URL=http://crawler:7000
   MODEL_URL=http://model:8000
   ```

3. Compose Docker container:

   ```sh
   docker compose up -d
   ```

4. The container exposes a web service on the HTTP port and can be access via:

   ```sh
   http://localhost/
   ```
