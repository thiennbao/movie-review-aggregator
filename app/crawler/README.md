# Movie Review Aggregator

## Crawler service

### How to run locally

1. Go into the server directory:

   ```sh
   cd app/crawler
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
   CHROMEDRIVER_PATH=<path_to_your_chromedriver.exe_file>
   ```

6. Start the service:

   ```sh
   fastapi dev app.py --host 0.0.0.0 --port 7000
   ```
