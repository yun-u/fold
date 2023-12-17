import functools
import logging
import re
import threading
import time
from typing import Callable, Dict, List, Literal, Optional, Sequence, Tuple, TypeVar
from urllib.parse import urljoin, urlparse

import rich
from bs4 import BeautifulSoup, Tag
from pydantic import (
    BaseModel,
    Field,
    HttpUrl,
    PrivateAttr,
    TypeAdapter,
    ValidationError,
    constr,
)
from rich.markup import escape
from rich.table import Table
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from app.document import Document

TWITTER_URL_PATTERN = re.compile(r"https:\/\/(twitter|x).com(?P<id>\/\w+\/status\/\d+)")
TWITTER_USER_ID_PATTERN = re.compile(
    r"(https:\/\/(twitter|x).com)?\/(?P<user_id>\w+)\/status\/\d+"
)

MAX_WAIT_TIME = 10

TextObject = Tuple[
    Literal["text", "link", "tag", "img", "emoji", "tweet-text-show-more-link"], str
]

T = TypeVar("T")


def scroll(
    driver: WebDriver,
    function: Optional[Callable[..., T]],
    condition_function: Callable[[T], bool],
    scroll_amount: float = 300.0,
    scroll_interval: float = 0.5,
) -> List[T]:
    results = []

    while True:
        results.append(function())

        if not condition_function(results[-1]):
            break

        prev_scroll_position = driver.execute_script("return window.pageYOffset;")

        driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
        time.sleep(scroll_interval)

        if prev_scroll_position == driver.execute_script("return window.pageYOffset;"):
            break

    return results


class TweetObject(BaseModel):
    id: constr(to_lower=True) = ""
    quote_id: constr(to_lower=True) = ""
    thread_ids: List[str] = Field(default_factory=list)
    texts: List[TextObject] = Field(default_factory=list)
    lang: str = ""
    user_name: str = ""
    user_id: constr(to_lower=True) = ""
    image_url: List[str] = Field(default_factory=list)
    video_url: str = ""
    video_thumbnail_url: str = ""
    card_url: str = ""

    _has_quote_tweet: PrivateAttr = False

    def print(self) -> None:
        table = Table(show_header=True, header_style="bold")
        table.add_column("Field", style="dim")
        table.add_column("Description")

        table.add_row("TweetID", self.id)
        table.add_row("QuoteID", self.quote_id)
        table.add_row("Has Quote", str(self._has_quote_tweet))
        table.add_row("Image URL", str(self.image_url))
        table.add_row(
            "Video URL",
            ", ".join(
                [i for i in (self.video_url, self.video_thumbnail_url) if i != ""]
            ),
        )
        table.add_row("Card URL", self.card_url)
        table.add_row(
            "User",
            ", ".join([i for i in (self.user_name, self.user_id) if i != ""]),
        )
        table.add_row("Lang", self.lang)

        texts = []
        for text_type, text in self.texts:
            if text_type == "link":
                texts.append(f"[blue]{escape(text)}[/blue]")
            else:
                texts.append(text)
        table.add_row("Text", "".join(texts))

        rich.print(table)

    @staticmethod
    def extract_full_url(link_text: str) -> str:
        if m := re.match(r"\[(.*)\]", link_text):
            return m.groups()[0]
        raise ValueError(link_text)

    def get_links(self) -> List[str]:
        links: List[str] = []

        if self.quote_id:
            links.append(urljoin(Twitter._URL, self.quote_id))

        if self.card_url:
            links.append(self.card_url)

        for text_type, text in self.texts:
            if text_type == "link":
                try:
                    url = self.extract_full_url(text)
                    links.append(str(TypeAdapter(HttpUrl).validate_python(url)))
                except ValidationError:
                    logging.warning(url)

        links = filter(lambda link: link != urljoin(Twitter._URL, self.id), links)

        return links

    def get_text(self) -> str:
        texts = []
        for text_type, text in self.texts:
            if text_type == "img":
                continue

            if text_type == "link":
                texts.append(self.extract_full_url(text))
            else:
                texts.append(text)

        return "".join(texts)

    def to_document(self) -> Document:
        metadata = self.model_dump(exclude=["id", "texts"])

        return Document(
            url=urljoin(Twitter._URL, self.id),
            category="tweet",
            links=self.get_links(),
            text=self.get_text(),
            metadata=metadata,
        )


def wait_and_find_elements(
    driver: WebDriver,
    by: str,
    value: str,
    condition: Callable[
        [Tuple[str, str]], Callable[[WebDriver], WebElement]
    ] = EC.presence_of_element_located,
    timeout: float = MAX_WAIT_TIME,
) -> List[WebElement]:
    wait = WebDriverWait(driver, timeout)
    wait.until(condition((by, value)))
    return driver.find_elements(by, value)


def send_text(element: WebElement, text: str) -> None:
    element.send_keys("")
    for t in text:
        time.sleep(0.1)
        element.send_keys(t)
    time.sleep(0.1)


class Twitter:
    _URL = "https://twitter.com"
    # _URL = "https://x.com"

    def __init__(self, headless: bool = True) -> None:
        self.headless = headless
        self.driver: Optional[WebDriver] = None
        self.lock = threading.Lock()

    def match(self, url: str) -> re.Match:
        return TWITTER_URL_PATTERN.match(url)

    def setup_driver(self) -> None:
        options = webdriver.FirefoxOptions()

        if self.headless:
            options.add_argument("-headless")

        self.driver = webdriver.Firefox(options=options)
        self.driver.implicitly_wait(10)

    ################################################################################
    # Login
    ################################################################################

    def login(self, user_id: str, password: str) -> None:
        if self.driver is None:
            self.setup_driver()

        logging.info("Start login.")

        self.open_login_page()
        self.enter_user_id(user_id)
        self.enter_password(password)
        self.click_login_button()

        logging.info("Login Succeeded.")

    def open_login_page(self):
        self.driver.get(urljoin(self._URL, "login"))
        time.sleep(5)

    def enter_user_id(self, user_id: str):
        input = wait_and_find_elements(
            self.driver, By.TAG_NAME, "input", EC.element_to_be_clickable
        )[0]
        send_text(input, user_id)
        input.send_keys(Keys.RETURN)

    def enter_password(self, password: str):
        input = wait_and_find_elements(
            self.driver,
            By.CSS_SELECTOR,
            "input[value='']",
            EC.element_to_be_clickable,
        )[0]
        send_text(input, password)

    def click_login_button(self):
        button = wait_and_find_elements(
            self.driver,
            By.XPATH,
            ".//span[contains(text(),'Log in')]",
            EC.element_to_be_clickable,
        )[0]
        button.click()

    ################################################################################
    # Scraping
    ################################################################################

    def validate_url(self, url: str) -> str:
        if match := TWITTER_URL_PATTERN.match(url):
            return urljoin(self._URL, match.groupdict()["id"]).lower()
        raise ValueError

    @staticmethod
    def extract_user_id(tweet_id_or_url: str) -> str:
        if m := TWITTER_USER_ID_PATTERN.match(tweet_id_or_url):
            return m.groupdict()["user_id"].lower()
        raise ValueError("Invalid tweet ID/URL format")

    @staticmethod
    def validate_user_tweets(
        tweet_object: Dict[str, TweetObject], user_id: str
    ) -> bool:
        """Validates if all tweets in the provided dictionary belong to the given user.

        Args:
            tweet_object (`Dict[str, TweetObject]`): A dictionary containing tweet IDs as keys
                                                     and corresponding TweetObject instances as values.
            user_id (`str`): The ID of the user to validate against.

        Returns:
            `bool`: True if all tweets in the dictionary belong to the given user, False otherwise.
        """
        for obj in tweet_object.values():
            # the collected user ID starts with @. So, we need to exclude that and compare.
            if user_id.lower() != obj.user_id[1:].lower():
                return False
        return True

    def fetch(self, url: str, verbose: bool = False) -> List[TweetObject]:
        url = self.validate_url(url)

        logging.info(f"Fetching '{url}'...")
        start_time = time.time()

        if self.driver is None:
            self.setup_driver()

        self.driver.get(url)

        wait_and_find_elements(self.driver, By.TAG_NAME, "body")

        merged: Dict[str, TweetObject] = {}
        for tweet_object in scroll(
            self.driver,
            function=self.fetch_tweet_object,
            condition_function=functools.partial(
                self.validate_user_tweets, user_id=self.extract_user_id(url)
            ),
        ):
            merged.update(tweet_object)

        # filter only Tweets from the original Tweet author.
        tweet_objects = self.filter_tweets_by_start_tweet_user_id(merged.values(), url)

        # fetch quote tweet
        self.add_quote_tweet_id(tweet_objects)

        # fetch long text
        self.replace_long_text(tweet_objects)

        self.add_thread_ids(tweet_objects)

        if verbose:
            for tweet_object in tweet_objects:
                tweet_object.print()

        elapsed_time = time.time() - start_time
        logging.info(f"Finished fetching '{url}' in {elapsed_time:.2f}s.")

        return tweet_objects

    def fetch_document(self, url: str) -> List[Document]:
        with self.lock:
            tweet_objects = self.fetch(url, verbose=True)

            documents = [obj.to_document() for obj in tweet_objects]

            for i in range(len(documents) - 1):
                documents[i].links.insert(0, documents[i + 1].url)

            return documents

    def filter_tweets_by_start_tweet_user_id(
        self, tweet_objects: Sequence[TweetObject], url: str
    ) -> List[TweetObject]:
        filtered_tweet_objects: List[TweetObject] = []

        start_tweet_id, user_id = urlparse(url).path, self.extract_user_id(url)

        pending = True
        for tweet_object in tweet_objects:
            if start_tweet_id == tweet_object.id:
                pending = False

            if pending:
                continue

            if user_id.lower() != tweet_object.user_id.lower():
                break

            filtered_tweet_objects.append(tweet_object)

        return filtered_tweet_objects

    def add_quote_tweet_id(self, tweet_objects: List[TweetObject]) -> None:
        for tweet_object in tweet_objects:
            if tweet_object._has_quote_tweet:
                tweet_object.quote_id = self.fetch_quote_tweet_id(tweet_object.id)

    def replace_long_text(self, tweet_objects: List[TweetObject]) -> None:
        for tweet_object in tweet_objects:
            if "tweet-text-show-more-link" in set([t[0] for t in tweet_object.texts]):
                tweet_object.texts = self.fetch_long_text(tweet_object.id)

    def add_thread_ids(self, tweet_objects: List[TweetObject]) -> None:
        thread_ids = [tweet_object.id for tweet_object in tweet_objects]
        for tweet_object in tweet_objects:
            tweet_object.thread_ids = thread_ids

    ################################################################################
    #  Quote Tweet
    ################################################################################

    def fetch_quote_tweet_id(self, tweet_id: str) -> str:
        self.driver.get(urljoin(self._URL, tweet_id))

        web_elements = self.driver.find_elements(By.XPATH, "//span[text()='Quote']")

        if len(web_elements) == 0:
            return ""

        web_elements[0].find_element(By.XPATH, "../..").click()

        quote_tweet_id = "/".join(
            urlparse(self.driver.current_url)
            ._replace(scheme="", netloc="")
            .geturl()
            .split("/")[:4]
        )

        return quote_tweet_id.lower()

    ################################################################################
    # Long Text Tweet
    ################################################################################

    def fetch_long_text(self, tweet_id: str) -> List[TextObject]:
        self.driver.get(urljoin(self._URL, tweet_id))

        tweet_object = self.fetch_tweet_object_by_id(tweet_id)
        assert tweet_object is not None, tweet_id

        return tweet_object.texts

    def fetch_tweet_object_by_id(self, tweet_id: str) -> Optional[TweetObject]:
        tweet_objects = self.fetch_tweet_object()
        return tweet_objects.get(tweet_id)

    ################################################################################
    # Default Tweet
    ################################################################################

    def fetch_tweet_object(self) -> Dict[str, TweetObject]:
        tweet_object_dict = {}
        for e in self.find_tweet_elements():
            tweet_object = self.get_tweet_object(e)
            tweet_object_dict[tweet_object.id] = tweet_object

        return tweet_object_dict

    def find_tweet_elements(self) -> List[Tag]:
        elements = []
        for element in wait_and_find_elements(self.driver, By.TAG_NAME, "article"):
            try:
                elements.append(
                    BeautifulSoup(element.get_attribute("outerHTML"), "html.parser")
                )
            except StaleElementReferenceException as e:
                logging.error(e)

        return elements

    def has_quote_tweet(self, element: Tag) -> bool:
        quote_texts = [
            tag
            for tag in element.find_all("span")
            if len(re.findall(r"\bQuote\b", tag.text)) > 0
        ]

        if len(quote_texts) > 0:
            return True
        return False

    def get_tweet_object(self, element: Tag) -> TweetObject:
        tweet_id = self.get_tweet_id(element)
        lang = self.get_tweet_lang(element)
        texts = self.get_tweet_texts(element)
        user_name, user_id = self.get_user_name_and_id(element)
        image_url = self.get_image_url(element)
        video_url, video_thumbnail_url = self.get_video_url(element)
        card_url = self.get_card_url(element)
        has_quote_tweet = self.has_quote_tweet(element)

        tweet_object = TweetObject(
            id=tweet_id,
            texts=texts,
            lang=lang,
            user_name=user_name,
            user_id=user_id,
            image_url=image_url,
            video_url=video_url,
            video_thumbnail_url=video_thumbnail_url,
            card_url=card_url,
        )
        tweet_object._has_quote_tweet = has_quote_tweet
        return tweet_object

    @staticmethod
    def get_tweet_lang(element: Tag) -> str:
        if tag := element.select_one("div[data-testid='tweetText']"):
            return tag["lang"]
        return ""

    @staticmethod
    def get_tweet_texts(element: Tag) -> List[TextObject]:
        if (tag := element.select_one("div[data-testid='tweetText']")) is None:
            return []

        texts = []
        for e in tag.children:
            if (tag := e.name) == "img":
                if alt := e.get("alt"):
                    texts.append(("emoji", alt))
            elif tag == "span" and e.get("data-testid") == "tweet-text-show-more-link":
                texts.append(("tweet-text-show-more-link", e.text))
            else:
                # link
                if e.name == "a":
                    # strip "…": 'HORIZONTAL ELLIPSIS' (U+2026)
                    if (url := e.text)[-1] == "\u2026":
                        url = url[:-1]

                    texts.append(("link", f"[{url}]({e.get('href')})"))
                # hashtag, usertag
                elif a := e.find("a"):
                    # <a/> tag can be a link to an image. If it is an image link, the text attribute is set to ""
                    if a.text != "":
                        texts.append(("tag", a.text))
                    else:
                        texts.append(("img", a.get("href")))
                else:
                    if e.text != "":
                        texts.append(("text", e.text))
        return texts

    @staticmethod
    def get_user_name_and_id(element: Tag) -> List[str]:
        if (tag := element.select_one("div[data-testid='User-Name']")) is None:
            return ["", ""]

        texts: List[str] = []
        for link in tag.find_all("a"):
            if span := link.find("span"):
                texts.append(span.text)

        # the collected user ID starts with @. So, we need to exclude that and compare.
        texts[1] = texts[1].lstrip("@").lower()

        return texts

    @staticmethod
    def get_video_url(element: Tag) -> Tuple[str, str]:
        if video := element.find("video"):
            thumbnail_url = video.get("poster", default="")
            url = video.get("src", default="")
            return url, thumbnail_url
        return "", ""

    @staticmethod
    def get_image_url(element: Tag) -> List[str]:
        if urls := list(
            map(
                lambda tag: tag["src"],
                filter(
                    lambda tag: tag["src"].startswith("https://pbs.twimg.com/media"),
                    element.find_all("img"),
                ),
            )
        ):
            return urls
        return []

    @staticmethod
    def get_card_url(element: Tag) -> str:
        if (tag := element.select_one("div[data-testid='card.wrapper']")) is None:
            return ""

        if s := tag.find("a"):
            return s.get("href")
        else:
            return ""

    @staticmethod
    def get_tweet_id(element: Tag) -> str:
        if tag := element.select_one("a > time"):
            # NOTE:
            # - "/<USER>/status/<ID>/history" or "/<USER>/status/<ID>"
            # - <USER> is case insensitive
            return "/".join(tag.parent["href"].split("/")[:4]).lower()
        return ""

    def quit(self):
        if self.driver:
            self.driver.quit()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.quit()
