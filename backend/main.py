from __future__ import annotations

import concurrent.futures
import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, List, Literal, Union
from urllib.parse import urljoin

import redis.asyncio as aioredis
import redis.exceptions
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import (
    BaseModel,
    Field,
    FileUrl,
    HttpUrl,
    field_validator,
)
from redis.client import Redis
from typing_extensions import Annotated, TypedDict
from ulid import ULID

from app import redis_pool
from app.document import Document
from app.document_processor import DocumentProcessorClientManager
from app.embedding_pipeline.pipeline import Pipeline
from app.embedding_pipeline.utils import validate_model_path
from app.search import (
    QueryModel,
    SearchResult,
    create_index,
    index_exists,
    original_post,
    search,
)
from app.sources import Twitter
from app.sources.twitter import TWITTER_URL_PATTERN
from app.utils.redis_utils import keyjoin
from app.utils.utils import OrderedSet

EMBEDDING_DIMENSION = int(os.environ["EMBEDDING_DIMENSION"])
INDEX_NAME = os.environ["INDEX_NAME"]
MODEL_ID = os.environ["MODEL_ID"]


redis_client = Redis(connection_pool=redis_pool.pool)
aioredis_client: Union[aioredis.Redis, None] = None
pipelines: Dict[str, Pipeline] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    global aioredis_client

    # Utilizing asyncio Redis requires an explicit disconnect of the connection since there is no asyncio deconstructor magic method.
    # By default, a connection pool is created on redis.Redis() and attached to this Redis instance.
    # The connection pool closes automatically on the call to Redis.close which disconnects all connections.
    aioredis_client = aioredis.Redis(decode_responses=True)

    if index_exists(redis_client):
        redis_client.ft(INDEX_NAME).dropindex(delete_documents=False)
    yield
    await aioredis_client.close()


app = FastAPI(lifespan=lifespan)


origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class EmbedRequest(BaseModel):
    url: Union[HttpUrl, FileUrl]

    @field_validator("url")
    @classmethod
    def validate_url(cls, url: Union[HttpUrl, FileUrl]) -> str:
        if match := TWITTER_URL_PATTERN.match(str(url)):
            return HttpUrl(urljoin(Twitter._URL, match.groupdict()["id"]))
        return url


@app.get("/ping")
async def ping():
    return "pong"


@app.post("/ping")
async def identity(item: Dict):
    return item


@app.post("/embed")
def embed(request: EmbedRequest):
    client = DocumentProcessorClientManager()

    try:
        model_path = validate_model_path(MODEL_ID)
    except FileNotFoundError as e:
        raise HTTPException(status_code=422, detail=str(e))

    links = client.request(
        url=str(request.url),
        model_path=model_path,
    )
    return {"links": links}


class WebPageMetadata(TypedDict):
    summary: str
    description: str


class ArxivMetadata(TypedDict):
    title: str
    authors: List[str]
    published: str
    summary: str


class Link(TypedDict):
    document_id: str
    url: str


class DocumentResponseModel(BaseModel):
    category: str
    created_at: str
    document_id: str
    metadata: Union[WebPageMetadata, ArxivMetadata, Dict] = Field(default_factory=dict)
    score: Union[float, None] = Field(None, ge=0.0, le=1.0)
    url: str
    is_read: bool
    is_bookmarked: bool
    links: List[Link] = Field(default_factory=list)
    backlinks: List[Link] = Field(default_factory=list)

    @staticmethod
    def get_links(
        direction: Literal["link", "backlink"],
        document_id: str,
        redis_client: Union[Redis, None] = None,
    ) -> List[Link]:
        if redis_client is None:
            redis_client = Redis(connection_pool=redis_pool.pool)

        links = []

        for link_id in redis_client.zrange(
            keyjoin(direction, document_id), 0, -1, desc=False
        ):
            if op := original_post(link_id, redis_client):
                links.append({"document_id": link_id, "url": op["url"]})

        links = list(OrderedSet(links, generate_key=lambda x: x["url"]))
        return links

    @staticmethod
    def get_merged_links(document: Document, redis_client: Union[Redis, None] = None):
        if redis_client is None:
            redis_client = Redis(connection_pool=redis_pool.pool)

        links = DocumentResponseModel.get_links("link", document.id, redis_client)

        if document.category == "tweet":
            thread_ids: List[str] = document.metadata["thread_ids"]

            for thread_id in thread_ids[1:]:
                if id := Document.url_to_id(
                    urljoin(Twitter._URL, thread_id), redis_client
                ):
                    links += DocumentResponseModel.get_links("link", id, redis_client)
                else:
                    logging.error(f"({document.id} ->){id} does not exist.")

            links = list(OrderedSet(links, generate_key=lambda x: x["url"]))
            return links

        return links

    @staticmethod
    def from_id(
        document_id: Union[str, ULID],
        score: Union[float, None] = None,
        redis_client: Union[Redis, None] = None,
    ) -> Union[DocumentResponseModel, None]:
        if redis_client is None:
            redis_client = Redis(connection_pool=redis_pool.pool)

        if (document := Document.from_id(document_id)) is None:
            return None

        if document.category == "webpage":
            metadata = {
                "author": document.metadata["author"],
                "title": document.metadata["title"],
                "description": document.metadata["description"],
                "logo": document.metadata["logo"],
                "image": document.metadata["image"],
            }
        elif document.category == "arxiv":
            metadata = {
                "authors": document.metadata["authors"],
                "published": document.metadata["published"],
                "summary": document.metadata["summary"],
                "title": document.metadata["title"],
            }
        elif document.category == "tweet":
            metadata = {"user_id": document.metadata["user_id"]}
        else:
            metadata = {}

        if document.category == "tweet":
            url = urljoin(Twitter._URL, document.metadata["thread_ids"][0])
        else:
            url = str(document.url)

        links = DocumentResponseModel.get_merged_links(document, redis_client)

        backlinks = DocumentResponseModel.get_links(
            "backlink", document_id, redis_client
        )

        return DocumentResponseModel(
            category=document.category,
            created_at=document.created_at,
            document_id=str(document_id),
            metadata=metadata,
            score=score,
            url=url,
            is_read=document.is_read,
            is_bookmarked=document.is_bookmarked,
            links=links,
            backlinks=backlinks,
        )

    @staticmethod
    def from_url(
        url: str,
        score: Union[float, None] = None,
        redis_client: Union[Redis, None] = None,
    ) -> Union[DocumentResponseModel, None]:
        if redis_client is None:
            redis_client = Redis(connection_pool=redis_pool.pool)

        if document_id := Document.url_to_id(url, redis_client):
            return DocumentResponseModel.from_id(document_id, score)

        return None

    @staticmethod
    def from_search_results(
        search_results: List[SearchResult], redis_client: Union[Redis, None] = None
    ) -> List[DocumentResponseModel]:
        if redis_client is None:
            redis_client = Redis(connection_pool=redis_pool.pool)

        def worker(search_result: SearchResult) -> DocumentResponseModel:
            return DocumentResponseModel.from_url(
                search_result.url, search_result.score, redis_client
            )

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=max(1, len(search_results))
        ) as executor:
            responses = executor.map(worker, search_results)
            responses = [response for response in responses if response is not None]

        return responses


class DocumentResponse(BaseModel):
    data: List[DocumentResponseModel]
    next_cursor: Union[int, None] = Field(ge=1)


@app.get(
    "/document",
    response_model=DocumentResponse,
    response_model_exclude_none=True,
)
def get_document(id: str):
    if response := DocumentResponseModel.from_id(id.upper(), redis_client=redis_client):
        return DocumentResponse(data=[response], next_cursor=None)
    return DocumentResponse(data=[], next_cursor=None)


class DeleteDocumentRequest(BaseModel):
    id: str


@app.delete("/document")
def delete_document(request: DeleteDocumentRequest):
    try:
        document = Document.from_id(request.id, redis_client)

        if document.category == "tweet":
            for thread_id in document.metadata.get("thread_ids", [])[1:]:
                if thread := Document.from_url(urljoin(Twitter._URL, thread_id)):
                    thread.delete()

        document.delete(redis_client)

        return {"success": True}
    except redis.exceptions.ResponseError as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.get(
    "/documents",
    response_model=DocumentResponse,
    response_model_exclude_none=True,
)
def get_documents(
    author: str = "",
    bookmarked: bool = False,
    category: Annotated[List[str], Query()] = [],
    desc: bool = False,
    text: str = "",
    title: str = "",
    unread: bool = False,
    vector_search: str = "",
    vector_search_document: str = "",
    model_id: str = MODEL_ID,
    offset: int = 0,
    count: Annotated[int, Query(ge=1)] = 10,
):
    # TODO: Escape special character e.g. "-"

    if category:
        if not set(category).issubset(["tweet", "webpage", "arxiv"]):
            raise HTTPException(
                status_code=422,
                detail="Invalid category specified. Please use a valid category: 'tweet', 'webpage', or 'arxiv'.",
            )
    else:
        category = ["tweet", "webpage", "arxiv"]

    try:
        model_path = validate_model_path(MODEL_ID)
    except FileNotFoundError as e:
        raise HTTPException(status_code=422, detail=str(e))

    global pipelines

    if not index_exists(INDEX_NAME):
        create_index(INDEX_NAME, model_path, EMBEDDING_DIMENSION, redis_client)

    if (pipeline := pipelines.get(model_id)) is None:
        pipeline = Pipeline(model_path)
        pipelines[model_id] = pipeline

    search_results, next_cursor = search(
        INDEX_NAME,
        QueryModel(
            author=author,
            bookmarked=bookmarked,
            category=category,
            desc=desc,
            text=text,
            title=title,
            unread=unread,
            vector_search=vector_search,
            vector_search_document=vector_search_document,
            offset=offset,
            count=count,
        ),
        pipeline,
        redis_client,
    )

    responses = DocumentResponseModel.from_search_results(search_results, redis_client)

    return DocumentResponse(data=responses, next_cursor=next_cursor)


class ActionRequest(BaseModel):
    id: str
    state: bool


@app.post("/read")
async def read(request: ActionRequest):
    try:
        await aioredis_client.json().set(
            keyjoin("document", request.id), "$.is_read", int(request.state)
        )
        return {"success": True}
    except redis.exceptions.ResponseError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        return {"success": False, "detail": str(e)}


@app.post("/bookmark")
async def bookmark(request: ActionRequest):
    try:
        await aioredis_client.json().set(
            keyjoin("document", request.id), "$.is_bookmarked", int(request.state)
        )
        return {"success": True}
    except redis.exceptions.ResponseError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        return {"success": False, "detail": str(e)}
