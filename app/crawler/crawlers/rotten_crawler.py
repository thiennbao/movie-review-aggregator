from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import (
    TimeoutException,
    ElementNotInteractableException,
    WebDriverException,
    NoSuchElementException
)
import time
from bs4 import BeautifulSoup
import os
import validators
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RottenTomatoesCrawler:
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
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--ignore-ssl-errors')
        chrome_options.add_argument('--enable-unsafe-swiftshader')
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
        """Fetch at least target_films films from Rotten Tomatoes by clicking 'Load More' until the target is met."""
        self.initialize_chrome_driver()

        # Load the initial page
        flag = False
        while not flag:
            try:
                self.browser.get(base_url)
                WebDriverWait(self.browser, 20).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "flex-container"))
                )
                flag = True
            except Exception as e:
                print(f"Error loading page: {e}. Retrying in 5 seconds...")
                time.sleep(5)

        # Initialize film list (no state loading)
        film_list = {}
        load_count = 0
        print(
            f"Starting fresh: {len(film_list)} films, clicked 'Load More' {load_count} times."
        )

        while len(film_list) < target_films:
            # Parse current page content
            soup = BeautifulSoup(self.browser.page_source, "lxml")
            poster_cards = soup.find_all("div", class_="flex-container")

            new_films_count = 0
            for poster_card in poster_cards:
                title_elem = poster_card.find("a")
                if title_elem:
                    sentiment_elem = title_elem.find("score-icon-critics")
                    if sentiment_elem and sentiment_elem.get("sentiment") == "empty":
                        print("Skipping empty sentiment film.")
                        continue
                    full_title = title_elem.find("span", class_="p--small").text.strip()
                    href_value = "https://www.rottentomatoes.com" + title_elem["href"]
                    if full_title not in film_list:
                        film_list[full_title] = href_value
                        new_films_count += 1
                        print(f"Title: {full_title}, Link: {href_value}")
                        if len(film_list) >= target_films:
                            break

            print(
                f"Load {load_count}: Added {new_films_count} new films. Total so far: {len(film_list)}"
            )

            if len(film_list) >= target_films:
                break

            # Try to load more films by clicking the "Load More" button
            try:
                load_more_button = WebDriverWait(self.browser, 20).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//button[@data-qa='dlp-load-more-button']")
                    )
                )
                self.browser.execute_script(
                    "arguments[0].scrollIntoView(true);", load_more_button
                )
                self.browser.execute_script("arguments[0].click();", load_more_button)
                print(f"Clicked 'Load More' (Load {load_count + 1})...")
                time.sleep(15)  # Wait for content to load

                # Scroll to bottom to ensure all content is loaded
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
                print(f"Error clicking 'Load More' or no more films to load: {e}")
                break

        self.close_browser()
        print(f"Finished crawling. Total films collected: {len(film_list)}")
        return film_list

    def convert_to_review_urls(self, movie_list: list) -> list:
        """Convert movie URLs to their review URLs based on role (critic or user)."""
        res = []
        for href in movie_list:
            if href[-1] != "/":
                href += "/"
            res.append({"href": href + "reviews"})
            res.append({"href": href + "reviews?type=user"})
        return res

    async def extract_review(self, review_card, movie_name: str, review_url: str, role: str) -> dict:
        """Extract review details from a review card."""
        review_data = review_card.find("div", class_="review-data")
        user_name = None
        try:
            user_name = (
                review_data.find(
                    "a",
                    class_="display-name" if role == "critic" else "audience-reviews__name",
                ).text.strip()
            )
        except AttributeError:
            user_name = (
                review_data.find(
                    "span",
                    class_="display-name" if role == "critic" else "audience-reviews__name",
                )
            )
            user_name = user_name.text.strip() if user_name else "No author name"

        sentiment_elem = review_data.find("score-icon-critics") if review_data else None
        sentiment = (
            sentiment_elem["sentiment"]
            if sentiment_elem and "sentiment" in sentiment_elem.attrs
            else "N/A"
        )
        comment = (
            review_card.find(
                "p",
                class_="review-text" if role == "critic" else "audience-reviews__review",
            ).text.strip()
            if review_card.find(
                "p",
                class_="review-text" if role == "critic" else "audience-reviews__review",
            )
            else "No review text"
        )
        review_date = None
        try:
            if role == "critic":
                review_date = review_card.find(
                    class_="original-score-and-url"
                ).find("span").text.strip()
            else:
                review_date = review_card.find(
                    "span",
                    class_="audience-reviews__duration"
                ).text.strip()
        except AttributeError:
            review_date = ""

        review = {
            "movie_name": movie_name,
            "author_name": user_name,
            "review": comment,
            "link": review_url.split("reviews")[0],
            "review_date": review_date,
            "sentiment": sentiment,
            "role": role,
        }

        return review

    # async def send_review_batch(self, reviews: list, batch_num: int, sio, sid: str) -> bool:
    #     """Send a batch of reviews via Socket.IO."""
    #     if not reviews:
    #         return True

    #     timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    #     logger.info(f"[{timestamp}] Preparing to send {len(reviews)} reviews (Batch {batch_num})")
    #     try:
    #         json_data = {"batch_num": batch_num, "reviews": reviews, "count": len(reviews)}
    #         json.dumps(json_data)  # Validate JSON serialization
    #         await sio.emit('review_batch', json_data, to=sid)
    #         logger.info(f"[{timestamp}] Sent {len(reviews)} reviews (Batch {batch_num})")
    #         # Note: Socket.IO doesn't require confirmation like WebSocket, but you can implement it if needed
    #         return True
    #     except Exception as e:
    #         logger.error(f"[{timestamp}] Error sending JSON: {e}")
    #         # await sio.emit('error', {"error": f"JSON send error: {str(e)}"}, to=sid)
    #         return False

    async def load_more_reviews(self, role) -> tuple[BeautifulSoup, bool]:
        """Click 'Load More' button and return updated page soup. Returns (soup, success)."""
        try:
            soup = BeautifulSoup(self.browser.page_source, "lxml")
            prev_review_count = len(soup.find_all(
                    "div",
                    class_="review-row" if role == "critic" else "audience-review-row",
            ))
            if not WebDriverWait(self.browser, 20).until(EC.element_to_be_clickable((By.CLASS_NAME, "load-more-container"))):
                logger.info("Load more button not clickable.")
                return BeautifulSoup(self.browser.page_source, "lxml"), False
            
            load_more = WebDriverWait(self.browser, 10).until(
                        EC.element_to_be_clickable(
                            (By.CLASS_NAME, "load-more-container")
            ))

            if not load_more.is_displayed() or not load_more.is_enabled():
                logger.info("Load more button not displayed or enabled.")
                return BeautifulSoup(self.browser.page_source, "lxml"), False
            
            self.browser.execute_script("arguments[0].scrollIntoView(true);", load_more)
            ActionChains(self.browser).move_to_element(load_more).click().perform()
            self.browser.execute_script("window.scrollBy(0, window.innerHeight);")
            time.sleep(5)

            soup = BeautifulSoup(self.browser.page_source, "lxml")
            new_review_count = len(soup.find_all(
                    "div",
                    class_="review-row" if role == "critic" else "audience-review-row",
            ))
            logger.info(f"INFO: prev_reviews {prev_review_count}, new_review_count {new_review_count}")
            # if new_review_count <= prev_review_count:
            #     logger.info("No new reviews loaded.")
            #     return BeautifulSoup(self.browser.page_source, "lxml"), False
            return BeautifulSoup(self.browser.page_source, "lxml"), True

        except (TimeoutException, ElementNotInteractableException, NoSuchElementException) as e:
            logger.info(f"Failed to load more reviews: {e}")
            return BeautifulSoup(self.browser.page_source, "lxml"), False

    async def get_reviews_api(self, review_url: str, reviews_range: list, role: str = "critic") -> None:
        """Fetch reviews for a specific movie from Rotten Tomatoes and send via Socket.IO."""
        if not validators.url(review_url):
            logger.error(f"Invalid URL provided: {review_url}")
            return

        try:
            all_reviews = []
            logger.info(f"Processing reviews for: {review_url}")
            self.initialize_chrome_driver()
            logger.info(f"Crawling reviews: {review_url}")

            start, end = reviews_range
            if start < 0 or end <= start:
                error_msg = "Invalid range provided. Start must be >= 0 and end must be > start."
                logger.error(error_msg)
                return

            start_idx = start
            page_size = 20
            target_reviews = end - start
            current_reviews = 0
            batch_num = 1
            roles = [role] if role == "user" else ["critic", "user"]
            role_urls = {
                "critic": review_url,
                "user": review_url + "?type=user" if "?type=user" not in review_url else review_url
            }

            for current_role in roles:
                role_url = role_urls[current_role]
                logger.info(f"Fetching {current_role} reviews: {role_url}")

                # Load the page with retry logic
                max_retries = 10
                for attempt in range(max_retries):
                    try:
                        if attempt > 0:
                            self.browser.refresh()
                            time.sleep(5)
                        else:
                            self.browser.get(role_url)
                        WebDriverWait(self.browser, 20).until(
                            EC.presence_of_element_located(
                                (
                                    By.CLASS_NAME,
                                    "review-row" if current_role == "critic" else "audience-review-row",
                                )
                            )
                        )
                        break
                    except TimeoutException as e:
                        logger.warning(
                            f"Timeout loading {current_role} review page: {e}. Retrying ({attempt + 1}/{max_retries})..."
                        )
                        time.sleep(5)
                    except WebDriverException as e:
                        logger.warning(
                            f"WebDriver error: {e}. Retrying ({attempt + 1}/{max_retries})..."
                        )
                        time.sleep(5)
                else:
                    error_msg = f"Failed to load {current_role} review page after {max_retries} attempts."
                    logger.error(error_msg)
                    return
                
                # await asyncio.sleep(10)

                # Skip to starting page
                skip_count = start // page_size if start % page_size != 0 or start == 0 else start // page_size - 1
                soup = BeautifulSoup(self.browser.page_source, "lxml")
                flag = False
                for i in range(skip_count):
                    soup, success = await self.load_more_reviews(current_role)
                    if not success:
                        logger.info(f"Not enough {current_role} reviews to skip. Only {i} clicks made.")
                        flag = True
                        review_cards = soup.find_all(
                            "div",
                            class_="review-row" if current_role == "critic" else "audience-review-row",
                        )
                        logger.info(f"Total {current_role} reviews: {len(review_cards)}")
                        break
                    logger.info(f"Skipped {current_role} page {i + 1}/{skip_count}")

                if flag and role == "critic":
                    start -= len(review_cards)
                    end -= len(review_cards)
                    start_idx = start
                    logger.info(f"Adjusted start index: {start_idx}, end index: {end}")
                    continue

                # Process initial reviews
                start_idx = start
                movie_name_elem = soup.find("a", class_="sidebar-title")
                movie_name = movie_name_elem.text.strip() if movie_name_elem else "Unknown Movie"
                review_cards = soup.find_all(
                    "div",
                    class_="review-row" if current_role == "critic" else "audience-review-row",
                )

                reviews = []
                for review_card in review_cards[start_idx:]:
                    if current_reviews >= target_reviews:
                        break
                    review = await self.extract_review(review_card, movie_name, role_url, current_role)
                    all_reviews.append(review)
                    reviews.append(review)
                    current_reviews += 1

                if reviews:
                    # if not await self.send_review_batch(reviews, batch_num, sio, sid):
                    #     return
                    batch_num += 1
                    start_idx += len(reviews)

                # Load additional pages
                while current_reviews < target_reviews:
                    soup, success = await self.load_more_reviews(current_role)
                    if not success:
                        logger.info(f"No more {current_role} reviews to load after {current_reviews} reviews")
                        break

                    movie_name_elem = soup.find("a", class_="sidebar-title")
                    movie_name = movie_name_elem.text.strip() if movie_name_elem else "Unknown Movie"
                    review_cards = soup.find_all(
                        "div",
                        class_="review-row" if current_role == "critic" else "audience-review-row",
                    )

                    reviews = []
                    for review_card in review_cards[start_idx:min(len(review_cards), start_idx + page_size)]:
                        review = await self.extract_review(review_card, movie_name, role_url, current_role)
                        reviews.append(review)
                        all_reviews.append(review)
                        current_reviews += 1
                        if current_reviews >= target_reviews:
                            break

                    if reviews:
                        # if not await self.send_review_batch(reviews, batch_num, sio, sid):
                        #     break
                        batch_num += 1
                        start_idx += len(reviews)

                if current_reviews >= target_reviews:
                    break

                review_cards = soup.find_all(
                    "div",
                    class_="review-row" if current_role == "critic" else "audience-review-row",
                )

                if current_role == "critic":
                    start = start - len(review_cards) if start - len(review_cards) > 0 else 0
                    end -= len(review_cards)
                    start_idx = start
                    print(start_idx, end)
            
            return all_reviews

        except Exception as e:
            logger.error(f"Error in get_reviews_ws: {e}")
        finally:
            self.close_browser()

if __name__ == "__main__":
    crawler = RottenTomatoesCrawler()
    # Test code remains unchanged