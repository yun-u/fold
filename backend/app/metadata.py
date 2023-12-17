from datetime import datetime
from typing import Union
from urllib.parse import urljoin

import requests
from pydantic import BaseModel, HttpUrl, TypeAdapter, ValidationError, field_validator
from selectolax.parser import HTMLParser


class Metadata(BaseModel):
    author: str = ""
    date: str = ""
    description: str = ""
    image: str = ""
    logo: str = ""
    publisher: str = ""
    title: str = ""
    url: str = ""

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: str) -> str:
        try:
            return TypeAdapter(datetime).validate_python(value).isoformat()
        except ValidationError:
            return value

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        try:
            return str(TypeAdapter(HttpUrl).validate_python(value))
        except ValidationError:
            return value


def scrape_metadata(url: str, content: Union[str, bytes, None] = None) -> Metadata:
    if content is None:
        try:
            res = requests.get(url)
            res.raise_for_status()
        except requests.HTTPError:
            res = requests.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
                },
            )
            res.raise_for_status()

        content = res.content

    tree = HTMLParser(content)

    def find(*queries: str, attribute: str = "content") -> str:
        for query in queries:
            if node := tree.css_first(query):
                if value := node.attributes.get(attribute):
                    return value
        return ""

    metadata = Metadata(
        author=find(
            "meta[property='article:author']",
            "meta[name='author']",
        ),
        date=find("meta[property='article:published_time']"),
        description=find(
            "meta[property='og:description']",
            "meta[name='twitter:description']",
            "meta[property='twitter:description']",
            "meta[name='description']",
        ),
        image=find(
            'meta[property="og:image:secure_url"]',
            'meta[property="og:image:url"]',
            'meta[property="og:image"]',
            'meta[name="twitter:image:src"]',
            'meta[property="twitter:image:src"]',
            'meta[name="twitter:image"]',
            'meta[property="twitter:image"]',
        ),
        logo=find("link[rel*='icon' i]", attribute="href"),
        publisher=find("meta[property='og:site_name']"),
        title=find(
            "meta[property='og:title']",
            "meta[name='twitter:title']",
            "meta[property='twitter:title']",
        ),
        url=find(
            "meta[property='og:url']",
            "meta[name='twitter:url']",
            "meta[property='twitter:url']",
        ),
    )

    if metadata.image != "":
        metadata.image = urljoin(urljoin(url, "/"), metadata.image)

    if metadata.logo != "":
        metadata.logo = urljoin(urljoin(url, "/"), metadata.logo)

    return metadata
