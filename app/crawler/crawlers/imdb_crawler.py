from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException, NoSuchElementException
import time
from bs4 import BeautifulSoup
import os
import logging
import asyncio

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IMDBCrawler:
    def __init__(
        self,
        chromedriver_path: str = os.getenv("CHROMEDRIVER_PATH", "C://Users//thiennbao//Downloads//chromedriver-win64//chromedriver.exe"),
        state_file: str = os.getenv("STATE_FILE", "rotten_state.json"),
    ):
        """Initialize the crawler with a path to chromedriver."""
        self.chromedriver_path = chromedriver_path
        self.state_file = state_file
        self.browser = None

    def initialize_chrome_driver(self) -> webdriver.Chrome:
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--ignore-ssl-errors')
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.7103.59 Safari/537.36"
        )
        service = Service(executable_path=self.chromedriver_path)
        try:
            self.browser = webdriver.Chrome(service=service, options=chrome_options)
        except WebDriverException as e:
            print(f"Failed to initialize ChromeDriver: {e}")
            raise
        return self.browser

    def close_browser(self):
        """Close the browser if it’s open."""
        if self.browser:
            self.browser.quit()
            self.browser = None

    def get_film_list(self, base_url: str, target_films: int = 100) -> dict:
        """Fetch at least target_films films from IMDb by clicking '50 more' until the target is met."""
        self.initialize_chrome_driver()
        self.browser.get(base_url)

        WebDriverWait(self.browser, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "ipc-title-link-wrapper"))
        )

        film_list = {}
        load_count = 0

        while len(film_list) < target_films:
            soup = BeautifulSoup(self.browser.page_source, "lxml")
            poster_cards = soup.find_all("a", class_="ipc-title-link-wrapper")

            new_films_count = 0
            for poster_card in poster_cards:
                title_elem = poster_card.find("h3")
                if title_elem:
                    full_title = title_elem.text.strip()
                    title = full_title.split(".", 1)[1].strip()
                    href_value = "https://www.imdb.com" + poster_card["href"]
                    if title not in film_list:
                        film_list[title] = href_value
                        new_films_count += 1
                        print(f"Title: {title}, Link: {href_value}")
                        if len(film_list) >= target_films:
                            break

            print(
                f"Load {load_count}: Added {new_films_count} new films. Total so far: {len(film_list)}"
            )

            if len(film_list) >= target_films:
                break

            try:
                see_more_button = WebDriverWait(self.browser, 20).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//button[contains(@class, 'ipc-see-more__button')]")
                    )
                )
                self.browser.execute_script(
                    "arguments[0].scrollIntoView(true);", see_more_button
                )
                self.browser.execute_script("arguments[0].click();", see_more_button)
                print(f"Clicked '50 more' (Load {load_count + 1})...")
                time.sleep(15)

                last_height = self.browser.execute_script(
                    "return document.body.scrollHeight"
                )
                while True:
                    self.browser.execute_script(
                        "window.scrollTo(0, document.body.scrollHeight);"
                    )
                    time.sleep(5)
                    new_height = self.browser.execute_script(
                        "return document.body.scrollHeight"
                    )
                    if new_height == last_height:
                        break
                    last_height = new_height

                load_count += 1
            except Exception as e:
                print(f"Error clicking '25 more' or no more films to load: {e}")
                break

        self.close_browser()
        print(f"Finished crawling. Total films collected: {len(film_list)}")
        return film_list

    def convert_to_review_url(self, movie_url: str) -> str:
        """Convert a movie URL to its reviews URL."""
        base_url = movie_url.split("?")[0] if "?" in movie_url else movie_url
        if base_url[-1] != "/":
            base_url += "/"
        return base_url + "reviews/"

    async def open_spoilers_and_parse_page(self, spoiler_selector: str, start_idx: int) -> tuple[BeautifulSoup, str]:
        """Open spoiler buttons starting from start_idx and parse the page with BeautifulSoup."""
        # Get all review cards using Selenium
        review_cards = self.browser.find_elements(By.CSS_SELECTOR, "article.user-review-item")

        if start_idx >= len(review_cards):
            logger.info(f"start_idx {start_idx} exceeds number of review cards {len(review_cards)}. Returning current page.")
            soup = BeautifulSoup(self.browser.page_source, "html.parser")
            movie_name_elem = soup.find("section", class_="ipc-page-section")
            movie_name = movie_name_elem.find("h2").text.strip() if movie_name_elem else "Unknown Movie"
            return soup, movie_name

        # Click spoiler buttons for review cards starting from start_idx
        for idx, review_card in enumerate(review_cards[start_idx:]):
            try:
                # Find the spoiler button within the review card
                spoiler_button = review_card.find_element(By.CLASS_NAME, spoiler_selector)
                if spoiler_button.is_displayed():
                    WebDriverWait(self.browser, 5).until(
                        EC.element_to_be_clickable(spoiler_button)
                    )
                    self.browser.execute_script("arguments[0].click();", spoiler_button)
                    # logger.info(f"Clicked spoiler button at index {start_idx + idx}")
            except (TimeoutException, NoSuchElementException):
                # logger.info(f"No clickable spoiler button at index {start_idx + idx}, continuing...")
                continue
            except Exception as e:
                logger.warning(f"Error clicking spoiler button at index {start_idx + idx}: {e}")
                continue

        # Parse the page after clicking spoilers
        soup = BeautifulSoup(self.browser.page_source, "html.parser")
        movie_name_elem = soup.find("section", class_="ipc-page-section")
        movie_name = movie_name_elem.find("h2").text.strip() if movie_name_elem else "Unknown Movie"
        return soup, movie_name

    async def extract_review(self, review_card, movie_name: str, movie_url: str) -> dict:
        """Extract review details from a review card."""
        review = review_card.find("div", class_="ipc-list-card__content")
        content_elem = review.find("div", class_="ipc-html-content-inner-div")
        content = content_elem.text.strip() if content_elem else "No Review"

        score_elem = review.find("span", class_="ipc-rating-star--rating")
        score = score_elem.text.strip() if score_elem else "No Score"

        review_author = review_card.find_all("li", class_="ipc-inline-list__item")
        author = (
            review_author[0].find("a").text.strip()
            if len(review_author) > 0 and review_author[0].find("a")
            else "No Author"
        )
        date = review_author[1].text.strip() if len(review_author) > 1 else None

        return {
            "movie_name": movie_name,
            "review": content,
            "score": score,
            "link": movie_url,
            "author_name": author,
            "review_date": date,
            "role": "user",
        }

    async def get_reviews_api(self, url: str, reviews_range: list) -> list:
        """Fetch reviews for a specific movie from IMDb and return as a list."""
        try:
            self.initialize_chrome_driver()
            logger.info(f"Opening URL: {url}")
            self.browser.get(url)
            WebDriverWait(self.browser, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, "ipc-page-section"))
            )

            start, end = reviews_range
            logger.info(f"Fetching reviews from {start} to {end}")
            if start < 0 or end < start:
                raise ValueError("Invalid range: start must be >= 0 and end >= start")

            page_size = 25
            skip_pages = start // page_size if start % page_size != 0 or start == 0 else (start // page_size) - 1
            target_reviews = end - start
            current_review_count = 0
            movie_url = url.split("?")[0].split("reviews")[0].rstrip('/')
            all_reviews = []

            for i in range(skip_pages):
                try:
                    span_element = WebDriverWait(self.browser, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "single-page-see-more-button"))
                    )
                    if not span_element.is_displayed():
                        logger.info(f"Span element not displayed, skipping page {i + 1}")
                        continue
                    button_inside_span = span_element.find_element(By.CLASS_NAME, "ipc-see-more__button")
                    self.browser.execute_script("arguments[0].scrollIntoView(true);", button_inside_span)
                    self.browser.execute_script("arguments[0].click();", button_inside_span)
                    time.sleep(5)
                    logger.info(f"Skipped page {i + 1}/{skip_pages}")
                except (TimeoutException, WebDriverException) as e:
                    logger.info(f"No more pages to skip after {i + 1} pages: {e}")
                    break

            start_idx = page_size * skip_pages
            if start > page_size * skip_pages:
                start_idx = start
            soup, movie_name = await self.open_spoilers_and_parse_page("review-spoiler-button", start_idx)
            review_cards = soup.find_all("article", class_="user-review-item")

            for review_card in review_cards[start_idx:]:
                if current_review_count >= target_reviews:
                    break
                review = await self.extract_review(review_card, movie_name, movie_url)
                all_reviews.append(review)
                current_review_count += 1

            while current_review_count < target_reviews:
                try:
                    span_element = WebDriverWait(self.browser, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "single-page-see-more-button"))
                    )
                    if not span_element.is_displayed():
                        logger.info("Span element not displayed, stopping loading more reviews")
                        break
                    button_inside_span = span_element.find_element(By.CLASS_NAME, "ipc-see-more__button")
                    self.browser.execute_script("arguments[0].scrollIntoView(true);", button_inside_span)
                    self.browser.execute_script("arguments[0].click();", button_inside_span)
                    time.sleep(5)
                    logger.info(f"Clicked 'See More' for page {(current_review_count // page_size) + skip_pages + 1}")
                except (TimeoutException, WebDriverException) as e:
                    logger.info(f"No more reviews to load after {current_review_count} reviews: {e}")
                    break

                soup, movie_name = await self.open_spoilers_and_parse_page("review-spoiler-button", start_idx)
                review_cards = soup.find_all("article", class_="user-review-item")
                logger.info(f"Curent review count: {current_review_count}")
                reviews = []
                for review_card in review_cards[start_idx:min(start_idx + page_size, len(review_cards))]:
                    review = await self.extract_review(review_card, movie_name, movie_url)
                    reviews.append(review)
                    all_reviews.append(review)
                    current_review_count += 1
                    if current_review_count >= target_reviews:
                        break
                logger.info(f"Curent review count: {current_review_count}")
                start_idx += len(reviews)

            return all_reviews

        except Exception as e:
            logger.error(f"Error in get_reviews_api: {e}")
            raise
        finally:
            self.close_browser()

if __name__ == "__main__":
    crawler = IMDBCrawler()
    review_url = crawler.convert_to_review_url("https://www.imdb.com/title/tt31806037/")
    # Test code for API method would require an async context