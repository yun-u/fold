from __future__ import annotations

import datetime
import io
import logging
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Union
from urllib.parse import urlparse

import feedparser
import pypdf
import requests
from pydantic import BaseModel, Field
from redis.client import Redis
from typing_extensions import Annotated

from app import redis_pool
from app.document import Document
from app.utils.pydantic_utils import instance_from_dict, instance_to_dict
from app.utils.redis_utils import keyjoin

ARXIV_URL_OR_ID_PATTERN = re.compile(
    r"(https?:\/\/arxiv.org\/(abs|pdf)\/)?(?P<id>\d+\.\d+(v|V)?\d+)"
)
ARXIV_VERSIONED_URL_OR_ID_PATTERN = re.compile(
    r"(https?:\/\/arxiv.org\/(abs|pdf)\/)?(?P<id>\d+\.\d+(v|V)\d+)"
)

ArxivUrlOrId = Annotated[str, Field(pattern=ARXIV_URL_OR_ID_PATTERN)]
ArxivVersionedUrlOrId = Annotated[str, Field(pattern=ARXIV_VERSIONED_URL_OR_ID_PATTERN)]


def change_url_scheme(url: str, scheme: str) -> str:
    return urlparse(url)._replace(scheme=scheme).geturl()


def timedelta_to_human_readable(timedelta_obj: datetime.timedelta) -> str:
    days = timedelta_obj.days
    hours, remainder = divmod(timedelta_obj.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    # Format the string
    time_str = ""
    if days:
        time_str += f"{days} day{'s' if days > 1 else ''} "
    if hours:
        time_str += f"{hours} hour{'s' if hours > 1 else ''} "
    if minutes:
        time_str += f"{minutes} minute{'s' if minutes > 1 else ''} "
    if seconds:
        time_str += f"{seconds} second{'s' if seconds > 1 else ''}"

    return time_str.strip()


class ArxivMetadataLink(BaseModel):
    """Represents a link within the metadata of an ArXiv article."""

    href: str  # URL of the link
    rel: str  # Relationship of the link to the article
    type: str  # MIME type of the link content
    title: str = ""  # Optional title of the link


class ArxivMetadata(BaseModel):
    """Represents the metadata of an ArXiv article."""

    title: str = ""  # Title of the article
    id: str = ""  # ArXiv ID of the article
    published: str = ""  # Publication date of the article
    updated: str = ""  # Last updated date of the article
    summary: str = ""  # Summary/abstract of the article
    authors: List[str] = Field(default_factory=list)  # List of authors' names
    # List of ArxivMetadataLink objects representing links
    links: List[ArxivMetadataLink] = Field(default_factory=list)
    # List of categories/subjects of the article
    categories: List[str] = Field(default_factory=list)
    comment: str = ""  # Additional comments on the article
    journal_ref: str = ""  # Journal reference of the article
    doi: str = ""  # Digital Object Identifier (DOI) of the article

    @staticmethod
    def parse(data: Union[str, bytes]) -> ArxivMetadata:
        """
        Parse ArXiv metadata from raw data (XML/HTML) using feedparser.

        Args:
            data (`Union[str, bytes]`): Raw data of the ArXiv article in XML/HTML format.

        Returns:
            `ArxivMetadata`: An instance of ArxivMetadata with parsed metadata.
        """
        d = feedparser.parse(data)
        entry = d.entries[0]
        return ArxivMetadata(
            title=entry.title,
            id=entry.id,
            published=entry.published,
            updated=entry.updated,
            summary=entry.summary,
            authors=[author["name"] for author in entry.authors],
            links=[
                ArxivMetadataLink(
                    href=link.href,
                    rel=link.rel,
                    type=link.type,
                    title=link.get("title", default=""),
                )
                for link in entry.links
            ],
            categories=[tag["term"] for tag in tags]
            if (tags := entry.get("tags"))
            else [],
            comment=entry.get("arxiv_comment", default=""),
            journal_ref=entry.get("arxiv_journal_ref", default=""),
            doi=entry.get("arxiv_doi", default=""),
        )


@dataclass
class ArxivObject:
    """Represents an ArXiv object with metadata and content."""

    metadata: ArxivMetadata  # Metadata of the ArXiv article
    content: bytes  # Raw content (PDF) of the ArXiv article

    def to_document(self) -> Document:
        reader = pypdf.PdfReader(io.BytesIO(self.content))
        text = "\n\n".join([page.extract_text() for page in reader.pages])

        return Document(
            url=change_url_scheme(self.metadata.id, "https"),
            category="arxiv",
            text=text,
            metadata=instance_to_dict(self.metadata),
        )


class Arxiv:
    """ArXiv API client and utility functions for working with ArXiv articles."""

    _API_URL = "http://export.arxiv.org/api/query"
    _PDF_URL = "https://arxiv.org/pdf/"
    _ABS_URL = "https://arxiv.org/abs/"

    def __init__(
        self,
        redis_client: Optional[Redis] = None,
        pdf_dir: Union[str, Path] = ".",
        latest_arxiv_id_version_cache_timeout: datetime.timedelta = datetime.timedelta(days=1),  # fmt: skip
    ) -> None:
        self.redis_client = (
            redis_client if redis_client else Redis(connection_pool=redis_pool.pool)
        )
        self.pdf_dir = Path(pdf_dir)
        self.latest_arxiv_id_version_cache_timeout = (
            latest_arxiv_id_version_cache_timeout
        )

    def match(self, url: str) -> re.Match:
        return ARXIV_URL_OR_ID_PATTERN.match(url)

    @staticmethod
    def get_arxiv_metadata_key(arxiv_id: str) -> str:
        return keyjoin("arxiv", "metadata", arxiv_id)

    def get_arxiv_pdf_path(self, arxiv_id_versioned: str) -> Path:
        self.validate_arxiv_id_versioned(arxiv_id_versioned)
        return self.pdf_dir / f"{arxiv_id_versioned}.pdf"

    @staticmethod
    def validate_arxiv_id_versioned(url_or_id: str) -> Optional[str]:
        if m := ARXIV_VERSIONED_URL_OR_ID_PATTERN.match(url_or_id):
            return m.groupdict()["id"].lower()
        return None

    @staticmethod
    def validate_arxiv_id(url_or_id: str) -> Optional[str]:
        if m := ARXIV_URL_OR_ID_PATTERN.match(url_or_id):
            return m.groupdict()["id"].lower()
        return None

    def get_arxiv_id(self, url: str) -> str:
        arxiv_id = self.validate_arxiv_id(url)
        assert arxiv_id is not None
        return arxiv_id

    def get_arxiv_id_versioned(self, url: str) -> str:
        if arxiv_id_versioned := self.validate_arxiv_id_versioned(url):
            return arxiv_id_versioned

        arxiv_id = self.validate_arxiv_id(url)
        return self.validate_arxiv_id_versioned(self.fetch_metadata(arxiv_id).id)

    def fetch_metadata(self, arxiv_id: str) -> ArxivMetadata:
        # ArXiv ID include both versioned and unversioned
        if value := self.redis_client.json().get(self.get_arxiv_metadata_key(arxiv_id)):
            logging.info(f"[{arxiv_id}] ArXiv metadata fetched from cache.")
            return instance_from_dict(ArxivMetadata, value)

        if (
            res := requests.get(self._API_URL, params={"id_list": arxiv_id})
        ).status_code != 200:
            raise RuntimeError(f"Failed to fetch metadata for ArXiv ID: {arxiv_id}")

        metadata = ArxivMetadata.parse(res.text)
        arxiv_id_versioned = self.validate_arxiv_id_versioned(metadata.id)

        self.redis_client.json().set(
            self.get_arxiv_metadata_key(arxiv_id_versioned),
            "$",
            metadata.model_dump(),
        )

        logging.info(
            f"[{arxiv_id_versioned}] Metadata for ArXiv ID has been fetched and cached."
        )

        # if ArXiv ID is unversioned
        if self.validate_arxiv_id_versioned(arxiv_id) is None:
            pipe = self.redis_client.pipeline(transaction=False)
            pipe.json().set(
                self.get_arxiv_metadata_key(arxiv_id), "$", metadata.model_dump()
            )
            pipe.expire(
                self.get_arxiv_metadata_key(arxiv_id),
                self.latest_arxiv_id_version_cache_timeout,
            )
            pipe.execute()

            logging.info(
                f"[{arxiv_id}] Metadata for unversioned ArXiv ID has been cached for {timedelta_to_human_readable(self.latest_arxiv_id_version_cache_timeout)}."
            )

        return metadata

    def fetch_pdf(self, arxiv_id_versioned: str) -> bytes:
        if (path := self.get_arxiv_pdf_path(arxiv_id_versioned)).exists():
            logging.info(f"[{arxiv_id_versioned}] PDF fetched from local cache.")
            return path.read_bytes()

        if (res := requests.get(self._PDF_URL + arxiv_id_versioned)).status_code != 200:
            raise RuntimeError(
                f"Failed to fetch PDF for ArXiv ID: {arxiv_id_versioned}"
            )

        path.write_bytes(res.content)

        return res.content

    def fetch(self, url: str) -> ArxivObject:
        logging.info(f"Fetching '{url}'...")
        start_time = time.time()

        arxiv_object = ArxivObject(
            metadata=self.fetch_metadata(self.get_arxiv_id(url)),
            content=self.fetch_pdf(self.get_arxiv_id_versioned(url)),
        )

        elapsed_time = time.time() - start_time
        logging.info(f"Finished fetching '{url}' in {elapsed_time:.2f}s.")

        return arxiv_object

    def fetch_document(self, url: str) -> Document:
        return self.fetch(url).to_document()
