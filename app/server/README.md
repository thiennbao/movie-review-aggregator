# Movie Review Aggregator

## Server side

### How to run locally

1. Go into the server directory:

   ```sh
   cd app/server
   ```

2. Create a virtual environment:

   ```sh
   python -m venv .venv
   ```

3. Activate the virtual environment:

   ```sh
   .\.venv\Scripts\activate # Windows
   ```

4. Install requirements:

   ```sh
   pip install -r requirements.txt
   ```

5. Create a file named `.env` following the format in `.env.template` file:

   ```xml
   POSTGRES_USER=<your_postgres_user>
   POSTGRES_HOST=<your_postgres_host>
   POSTGRES_PASSWORD=<your_postgres_password>
   POSTGRES_DATABASE=<your_postgres_database_name>
   DB_PORT=<your_postgres_port>

   MODEL_URL=http://localhost:8000
   CRAWLER_URL=http://localhost:7000
   ```

6. Start the server:

   ```sh
   flask run --debug
   ```
