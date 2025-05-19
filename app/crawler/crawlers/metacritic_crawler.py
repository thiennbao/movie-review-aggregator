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
from datetime import datetime
import validators
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MetacriticCrawler:
    def __init__(
        self,
        chromedriver_path: str = os.getenv("CHROMEDRIVER_PATH"),
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

    def get_movie_list(
        self, base_url: str, start_page: int = 1, min_movies: int = 100
    ) -> dict:
        """Fetch a list of movies from Metacritic until at least min_movies are collected."""
        movie_list = {}
        page = start_page

        while len(movie_list) < min_movies:
            self.initialize_chrome_driver()
            url = base_url + str(page)
            print(f"Crawling page {page}: {url}")

            try:
                self.browser.get(url)
                WebDriverWait(self.browser, 20).until(
                    EC.presence_of_element_located(
                        (By.CLASS_NAME, "c-finderProductCard_container")
                    )
                )
            except Exception as e:
                print(f"Error loading page {page}: {e}. Retrying in 10 seconds...")
                time.sleep(10)
                self.browser.get(url)
                WebDriverWait(self.browser, 20).until(
                    EC.presence_of_element_located(
                        (By.CLASS_NAME, "c-finderProductCard_container")
                    )
                )

            soup = BeautifulSoup(self.browser.page_source, "lxml")
            poster_cards = soup.find_all("a", class_="c-finderProductCard_container")

            new_movies_count = 0
            for poster_card in poster_cards:
                if poster_card and poster_card.find(
                    "div", class_="c-siteReviewScore_background"
                ):
                    href_value = "https://www.metacritic.com" + poster_card["href"]
                    title_elem = poster_card.find("h3")
                    if title_elem:
                        spans = title_elem.find_all("span")
                        if len(spans) > 1:
                            title = spans[1].text.strip()
                        else:
                            title = spans[0].text.strip()
                        if title not in movie_list:  # Avoid duplicates
                            movie_list[title] = href_value
                            new_movies_count += 1
                            print(f"Title: {title}, Link: {href_value}")
                            if(len(movie_list) >= min_movies):
                                break

            self.close_browser()
            print(
                f"Found {new_movies_count} new movies on page {page}. Total so far: {len(movie_list)}"
            )

            if new_movies_count == 0:  # No new movies found, end of list
                print(f"No new movies found on page {page}. Stopping crawl.")
                break

            page += 1  # Move to the next page

        print(f"Finished crawling. Total movies collected: {len(movie_list)}")
        return movie_list

    def convert_to_review_urls(self, movie_list: list) -> list:
        """Convert movie URLs to their critic review URLs."""
        res = []
        for href in movie_list:
            if not href.endswith("/"):
                href += "/"
            res.append({"href": href + "critic-reviews/"})
            res.append({"href": href + "user-reviews/"})
        return res

    def close_modal(self):
        """Close the modal by clicking the SVG close button."""
        try:
            logger.info("Attempting to close modal")
            close_button_wrapper = WebDriverWait(self.browser, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "c-globalModal_closeButtonWrapper"))
            )
            close_button_wrapper.click()
            logger.info("Modal closed successfully")
        except (TimeoutException, NoSuchElementException) as e:
            logger.warning(f"No modal to close or failed to close modal: {e}")
        except Exception as e:
            logger.error(f"Unexpected error closing modal: {e}")

    def handle_spoiler(self, comment_card) -> str:
        """Handle spoilers in the comment by clicking 'Read More' and closing any modal."""
        logger.info("Detected spoiler alert in comment")
        try:
            read_more = comment_card.find("button", class_="c-globalButton_container")
            read_more.click()
            time.sleep(2)
            logger.info("Clicked 'Read More' to reveal spoiler content")

            WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "c-siteReviewReadMore_wrapper"))
            )

            soup = BeautifulSoup(self.browser.page_source, "lxml")
            updated_comment_card = soup.find("div", class_="c-siteReviewReadMore_wrapper")
            if updated_comment_card:
                full_comment = updated_comment_card.text.strip()
                logger.info(f"Comment after handling spoiler: {full_comment}")
                self.close_modal()
                return full_comment
            else:
                logger.warning("Failed to find updated comment after clicking 'Read More'")
                return "No review text"

        except TimeoutException as e:
            logger.error(f"Timeout while handling spoiler: {e}")
            return "No review text"
        except Exception as e:
            logger.error(f"Error handling spoiler: {e}")
            return "No review text"

    # async def send_periodic_notification(self, sio, sid, interval=55):
    #     """Send periodic notifications via Socket.IO."""
    #     try:
    #         while True:
    #             await sio.emit('info', {"INFO": "Still waiting for page to load..."}, to=sid)
    #             await asyncio.sleep(interval)
    #     except asyncio.CancelledError:
    #         await sio.emit('info', {"INFO": "Periodic notification stopped"}, to=sid)
    #         raise

    # async def keep_alive(self, sio, sid):
    #     """Send ping messages to keep Socket.IO connection alive."""
    #     try:
    #         while True:
    #             await asyncio.sleep(15)
    #             await sio.emit('ping', {}, to=sid)
    #             logger.debug("Sent ping to keep Socket.IO alive")
    #     except Exception as e:
    #         logger.warning(f"Keep-alive ping failed: {str(e)}")

    async def get_reviews_api(self, review_url: str, reviews_range: list, role: str = "critic") -> None:
        """Fetch reviews for a specific movie from Metacritic and send via Socket.IO."""
        if not validators.url(review_url):
            logger.error(f"Invalid URL provided: {review_url}")
            return

        try:
            all_reviews = []
            logger.info(f"Processing reviews for: {review_url}")
            self.initialize_chrome_driver()

            word_split = "critic-reviews" if role == "critic" else "user-reviews"
            movie_url = review_url.split(word_split)[0]
            logger.info(f"Crawling reviews for: {movie_url}")
            roles = [role] if role == "user" else ["critic", "user"]
            role_urls = {
                "critic": review_url,
                "user": review_url.replace("critic-reviews", "user-reviews")
            }

            start, end = reviews_range
            if start < 0 or end <= start:
                error_msg = "Invalid range provided. Start must be >= 0 and end > start."
                logger.error(error_msg)
                return

            target_reviews = end - start
            total_reviews_processed = 0
            batch_num = 1

            for current_role in roles:
                role_url = role_urls[current_role]
                logger.info(f"Fetching {current_role} reviews: {role_url}")

                try:
                    self.browser.get(role_url)
                    WebDriverWait(self.browser, 30).until(
                            EC.presence_of_element_located((By.CLASS_NAME, "c-siteReview_main"))
                    )
                except TimeoutException:
                    try:
                        if WebDriverWait(self.browser, 60).until(
                            EC.presence_of_element_located((By.CLASS_NAME, "c-pageProductReviews_message"))
                        ):
                            logger.info(f"No {current_role} reviews available")
                            continue
                    except TimeoutException:
                        logger.error("Failed to load review page")
                        return

                page_size = 50
                max_scroll_attempts = 50
                scroll_attempts = 0

                skip_count = start // page_size if start % page_size != 0 else start // page_size - 1
                current_reviews = 0
                for _ in range(max(0, skip_count)):
                    soup = BeautifulSoup(self.browser.page_source, "lxml")
                    review_cards = soup.find_all("div", class_="c-siteReview")
                    current_reviews = len(review_cards)
                    self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(5)
                    new_soup = BeautifulSoup(self.browser.page_source, "lxml")
                    new_review_cards = new_soup.find_all("div", class_="c-siteReview")
                    if len(new_review_cards) <= current_reviews:
                        logger.info(f"Reached the end of reviews for {current_role} role during skipping")
                        break
                    scroll_attempts += 1
                    logger.info(f"Skipped scroll {scroll_attempts}/{skip_count}")

                soup = BeautifulSoup(self.browser.page_source, "lxml")
                movie_name_elem = soup.find("a", class_="c-productSubpageHeader_back")
                if not movie_name_elem:
                    movie_name_elem = soup.find("span", class_="c-productSubpageHeader_back")
                if not movie_name_elem:
                    logger.error("Failed to find movie name")
                    break
                movie_name = movie_name_elem.text.strip()

                review_cards = soup.find_all("div", class_="c-siteReview")
                if len(review_cards) <= start and total_reviews_processed == 0:
                    start = start - len(review_cards) if start - len(review_cards) > 0 else 0
                    end = end - len(review_cards)
                    logger.info(f"Adjusted start and end indices: {start}, {end}")
                    logger.info(f"Not enough {current_role} reviews to fulfill range")
                    continue

                start_idx = start
                reviews = []
                for review_card in review_cards[start_idx:min(end, len(review_cards))]:
                    if total_reviews_processed >= target_reviews:
                        break

                    body = review_card.find("div", class_="c-siteReview_main")
                    score_card = body.find("div", class_="c-siteReviewHeader_reviewScore")
                    score = score_card.find("span").text.strip() if score_card else "N/A"

                    comment_card = body.find("div", class_="c-siteReview_quote")
                    comment = (
                        comment_card.find("span").text.strip()
                        if comment_card
                        else "No review text"
                    )
                    if "[SPOILER ALERT: This review contains spoilers.]" in comment:
                        comment = self.handle_spoiler(comment_card=body)

                    date = "N/A"
                    date_elem = body.find("div", class_="c-siteReviewHeader_reviewDate")
                    if date_elem:
                        date = date_elem.text.strip()

                    try:
                        author = review_card.find(
                            "a", class_="c-siteReview_criticName" if current_role == "critic" else "c-siteReviewHeader_username"
                        )
                        if current_role == "critic" and author:
                            author = author.text.strip()[3:]
                        elif current_role == "user" and author:
                            author = author.text.strip()
                    except AttributeError:
                        author = review_card.find(
                            "span", class_="c-siteReview_criticName" if current_role == "critic" else "c-siteReviewHeader_username"
                        )
                        if current_role == "critic" and author:
                            author = author.text.strip()[3:]
                        elif current_role == "user" and author:
                            author = author.text.strip()

                    review = {
                            "movie_name": movie_name,
                            "review": comment,
                            "score": score,
                            "link": movie_url,
                            "author_name": author,
                            "review_date": date if date != "N/A" and date != "" else None,
                            "role": current_role,
                    }
                    all_reviews.append(review)
                    reviews.append(review)
                    total_reviews_processed += 1
                    start_idx += 1

                if reviews:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
                    # logger.info(f"[{timestamp}] Preparing to send {len(reviews)} reviews (Batch {batch_num})")
                    try:
                        # json_data = {"batch_num": batch_num, "reviews": reviews, "count": len(reviews)}
                        # json.dumps(json_data)
                        # await sio.emit('review_batch', json_data, to=sid)
                        # logger.info(f"[{timestamp}] Sent {len(reviews)} reviews (Batch {batch_num})")
                        batch_num += 1
                        start_idx += len(reviews)
                    except Exception as e:
                        logger.error(f"[{timestamp}] Error sending JSON: {e}")
                        break

                while total_reviews_processed < target_reviews and scroll_attempts < max_scroll_attempts:
                    current_reviews = len(review_cards)
                    self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(5)
                    soup = BeautifulSoup(self.browser.page_source, "lxml")
                    review_cards = soup.find_all("div", class_="c-siteReview")

                    print(f"Current reviews count: {len(review_cards)}")

                    if len(review_cards) <= current_reviews:
                        logger.info(f"Reached the end of reviews for {current_role} role after {scroll_attempts + 1} scrolls")
                        break

                    movie_name_elem = soup.find("a", class_="c-productSubpageHeader_back")
                    if not movie_name_elem:
                        movie_name_elem = soup.find("span", class_="c-productSubpageHeader_back")
                    if not movie_name_elem:
                        logger.error("Failed to find movie name")
                        break
                    movie_name = movie_name_elem.text.strip()

                    reviews = []
                    for review_card in review_cards[start_idx:min(end, len(review_cards))]:
                        if total_reviews_processed >= target_reviews:
                            break

                        body = review_card.find("div", class_="c-siteReview_main")
                        score_card = body.find("div", class_="c-siteReviewHeader_reviewScore")
                        score = score_card.find("span").text.strip() if score_card else "N/A"

                        comment_card = body.find("div", class_="c-siteReview_quote")
                        comment = (
                            comment_card.find("span").text.strip()
                            if comment_card
                            else "No review text"
                        )
                        if "[SPOILER ALERT: This review contains spoilers.]" in comment:
                            comment = self.handle_spoiler(comment_card=body)

                        date = "N/A"
                        date_elem = body.find("div", class_="c-siteReviewHeader_reviewDate")
                        if date_elem:
                            date = date_elem.text.strip()

                        try:
                            author = review_card.find(
                                "a", class_="c-siteReview_criticName" if current_role == "critic" else "c-siteReviewHeader_username"
                            )
                            if current_role == "critic" and author:
                                author = author.text.strip()[3:]
                            elif current_role == "user" and author:
                                author = author.text.strip()
                        except AttributeError:
                            author = review_card.find(
                                "span", class_="c-siteReview_criticName" if current_role == "critic" else "c-siteReviewHeader_username"
                            )
                            if current_role == "critic" and author:
                                author = author.text.strip()[3:]
                            elif current_role == "user" and author:
                                author = author.text.strip()

                        review = {
                                "movie_name": movie_name,
                                "review": comment,
                                "score": score,
                                "link": movie_url,
                                "author_name": author,
                                "review_date": date if date != "N/A" and date != "" else None,
                                "role": current_role,
                        }

                        reviews.append(review)
                        all_reviews.append(review)
                        total_reviews_processed += 1
                        start_idx += 1
                        
                        if total_reviews_processed >= target_reviews:
                            break

                    if reviews:
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
                        logger.info(f"[{timestamp}] Preparing to send {len(reviews)} reviews (Batch {batch_num})")
                        try:
                            # json_data = {"batch_num": batch_num, "reviews": reviews, "count": len(reviews)}
                            # json.dumps(json_data)
                            # await sio.emit('review_batch', json_data, to=sid)
                            logger.info(f"[{timestamp}] Sent {len(reviews)} reviews (Batch {batch_num})")
                            batch_num += 1
                            start_idx += len(reviews)
                        except Exception as e:
                            logger.error(f"[{timestamp}] Error sending JSON: {e}")
                            break

                    scroll_attempts += 1
                    logger.info(f"Scroll attempt {scroll_attempts + 1}/{max_scroll_attempts}")

                soup = BeautifulSoup(self.browser.page_source, "lxml")
                review_cards = soup.find_all("div", class_="c-siteReview")
                if total_reviews_processed < target_reviews and current_role == "critic":
                    start = start - len(review_cards) if start - len(review_cards) > 0 else 0
                    end = end - len(review_cards)
                    start_idx = start
                if total_reviews_processed >= target_reviews:
                    break
            return all_reviews

        except Exception as e:
            logger.error(f"Error in get_reviews_ws: {e}")
        finally:
            self.close_browser()

if __name__ == "__main__":
    crawler = MetacriticCrawler()
    # Test code remains unchanged