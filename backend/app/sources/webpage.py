from __future__ import annotations

import html.parser
import logging
import re
import threading
import time
from dataclasses import InitVar, dataclass, field
from typing import Iterator, List, Optional, Sequence, Set, Tuple, Union

import requests
import selectolax.parser
from pydantic import BaseModel, ConfigDict, HttpUrl

from app.document import Document
from app.metadata import Metadata, scrape_metadata
from app.utils.pydantic_utils import instance_to_dict

WEBPAGE_URL_PATTERN = re.compile(
    r"(?P<id>https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b("  # Matches webpage URLs
    r"[-a-zA-Z0-9()@:%_\+.~#?&//=]*))"
)

ROOT_TAG_OF_SITE = {re.compile(r"https:\/\/github.com\/"): "article"}

INCLUDE_TAG = [
    "p",
    "pre",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "ul",
    "ol",
    "li",
    "blockquote",
    "code",
]
EXCLUDE_TAG = ["head", "footer", "nav", "script", "aside"]


@dataclass
class Node:
    id: int = 0
    line: int = 0
    col: int = 0
    parent: InitVar[Optional[TagNode]] = None

    def __eq__(self, other: Node) -> bool:
        return self.id == other.id

    def __iter__(self) -> Iterator[Node]:
        raise NotImplementedError

    def to_text(self, markdown_syntax: bool) -> str:
        raise NotImplementedError

    def search_by_id(self, id: int) -> Optional[Node]:
        if self.id == id:
            return self

        if hasattr(self, "children"):
            for c in self.children:
                if node := c.search_by_id(id):
                    return node
        return None

    def remove(self) -> None:
        try:
            if self.parent:
                i = self.parent.children.index(self)
                self.parent.children.pop(i)
        except ValueError:
            pass


@dataclass
class MarkdownProperty:
    # List
    mark: str = ""

    # Code Block
    language_id: str = ""


@dataclass
class TagNode(Node):
    tag: str = ""
    attrs: List[Tuple[str, str]] = field(default_factory=list)
    children: List[Node] = field(default_factory=list)

    _whitespace: InitVar[str] = ""
    mark: InitVar[str] = ""
    code_language_id: InitVar[str] = ""

    def __iter__(self) -> Iterator[Node]:
        yield self
        for c in self.children:
            yield from c

    @staticmethod
    def whitespace(tag) -> str:
        if tag in ("code", "span"):
            whitespace = ""
        elif tag in ("ul", "ol", "li"):
            whitespace = "\n"
        elif tag in ("p", "pre") or re.match(r"h(\d)", tag):
            whitespace = "\n\n"
        else:
            whitespace = ""
        return whitespace

    def apply_markdown_syntax(self, text: str) -> str:
        if self.tag == "code" and self.search_ascendant("pre") is None:
            text = f"`{text}`"
        elif self.tag == "pre":
            text = f"```{self.code_language_id}\n{text}\n```"
        elif self.tag == "blockquote":
            text = text.lstrip("\n")
            text = f"> {text}"
        elif self.tag == "strong":
            text = f"**{text}**"
        elif self.tag == "em":
            text = f"*{text}*"
        elif m := re.match(r"h(\d)", self.tag):
            i = int(m.groups()[0])
            text = f"{'#' * i} {text}"
        return text

    def to_text(self, markdown_syntax: bool) -> str:
        text = "".join([c.to_text(markdown_syntax) for c in self.children])

        if markdown_syntax:
            text = self.apply_markdown_syntax(text)

        whitespace = self._whitespace if self._whitespace else self.whitespace(self.tag)

        return self.mark + text + whitespace

    def search_by_tag(
        self, tag: Union[str, Sequence[str]], recursive: bool = False
    ) -> List[TagNode]:
        if isinstance(tag, str):
            tag = [tag]

        tag_nodes = []

        if self.tag in tag:
            tag_nodes.append(self)
            if not recursive:
                # Only 1 depth
                return tag_nodes

        if self.children:
            for c in self.children:
                if not isinstance(c, TagNode):
                    continue

                if node := c.search_by_tag(tag, recursive):
                    tag_nodes.extend(node)
        return tag_nodes

    def search_ascendant(self, tag: Union[str, Sequence[str]]) -> TagNode:
        if isinstance(tag, str):
            tag = [tag]

        if self.parent and isinstance(self.parent, TagNode):
            if self.parent.tag in tag:
                return self.parent
            return self.parent.search_ascendant(tag)
        return None


@dataclass
class TextNode(Node):
    text: str = ""

    def __iter__(self) -> Iterator[Node]:
        yield self

    def to_text(self, markdown_syntax: bool) -> str:
        return self.text


class HTMLParser(html.parser.HTMLParser):
    def __init__(
        self,
        include_tag: Set[str],
        exclude_tag: Set[str],
        *,
        convert_charrefs: bool = True,
    ) -> None:
        super().__init__(convert_charrefs=convert_charrefs)

        self.data = None

        self.include_tag = include_tag
        self.exclude_tag = exclude_tag

        self.root = TagNode()
        self.tag_nodes: List[TagNode] = [self.root]
        self.id = 0
        self.line = 0
        self.col = 0

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, str]]):
        self.id += 1
        self.line += 1
        self.col += 1

        tag_node = TagNode(
            id=self.id, line=self.line, col=self.col, tag=tag, attrs=attrs
        )

        if self.tag_nodes:
            cur_node = self.tag_nodes[-1]
            cur_node.children.append(tag_node)
            tag_node.parent = cur_node

        self.tag_nodes.append(tag_node)

    def handle_endtag(self, tag: str):
        if self.tag_nodes:
            while (tag_node := self.tag_nodes.pop()).tag != tag:  # noqa: F841
                pass

    def handle_data(self, data: str):
        self.id += 1
        self.line += 1

        if self.tag_nodes:
            cur_node = self.tag_nodes[-1]
            text_node = TextNode(
                id=self.id, line=self.line, col=self.col + 1, text=data
            )
            cur_node.children.append(text_node)
            text_node.parent = cur_node

    def prepare(self) -> None:
        self.prepare_mark()
        self.prepare_code_language_id()
        self.prepare_whitespace()

    def prepare_mark(self) -> None:
        for ol in self.root.search_by_tag("ol"):
            for i, li in enumerate(ol.search_by_tag("li")):
                li.mark = f"{i + 1}. "

        for ul in self.root.search_by_tag("ul"):
            for li in ul.search_by_tag("li"):
                li.mark = "- "

    def prepare_code_language_id(self) -> None:
        for pre in self.root.search_by_tag("pre"):
            if (
                pre.children
                and isinstance((div := pre.children[0]), TagNode)
                and div.tag == "div"
                and ("class", "language-id") in div.attrs
            ):
                pre.code_language_id = div.to_text(False)
                div.remove()

    def prepare_whitespace(self) -> None:
        for code in self.root.search_by_tag("code"):
            for div in code.children:
                if isinstance(div, TagNode):
                    for attr_name, attr_value in div.attrs:
                        if attr_name == "class" and re.match(".*line", attr_value):
                            div._whitespace = "\n"

    def to_text(self, markdown_syntax: bool = False) -> str:
        return "\n\n".join(
            [
                n.to_text(markdown_syntax).strip()
                for n in self.root.search_by_tag(self.include_tag)
            ]
        ).strip()

    def to_markdown(self) -> str:
        return self.to_text(True)

    def remove_tag(self) -> None:
        for n in self.root.search_by_tag(self.exclude_tag):
            n.remove()

    def feed(self, data: str) -> None:
        super().feed(data)
        self.data = data
        self.remove_tag()
        self.prepare()


class WebPageObject(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    url: HttpUrl
    metadata: Metadata
    parser: HTMLParser

    def to_document(self) -> Document:
        text = self.parser.to_text()
        return Document(
            url=self.url,
            category="webpage",
            text=text,
            metadata=instance_to_dict(self.metadata),
        )


class WebPage:
    def __init__(
        self,
        include_tag: Optional[Set[str]] = None,
        exclude_tag: Optional[Set[str]] = None,
        headless: bool = True,
    ) -> None:
        self.include_tag = INCLUDE_TAG if include_tag is None else include_tag
        self.exclude_tag = EXCLUDE_TAG if exclude_tag is None else exclude_tag
        self.headless = headless
        self.lock = threading.Lock()

    def match(self, url: str) -> re.Match:
        return WEBPAGE_URL_PATTERN.match(url)

    @staticmethod
    def get_root_tag(url: str) -> str:
        for pattern, tag in ROOT_TAG_OF_SITE.items():
            if pattern.match(url):
                return tag
        return "body"

    def get_outer_html(self, content: Union[str, bytes], tag: str) -> str:
        outer_html = selectolax.parser.HTMLParser(content).css_first(tag).html
        assert outer_html is not None
        return str(outer_html)

    def fetch(self, url: str) -> WebPageObject:
        logging.info(f"Fetching '{url}'...")
        start_time = time.time()

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

        metadata = scrape_metadata(url, res.content)
        outer_html = self.get_outer_html(
            res.content, self.get_root_tag(metadata.url or url)
        )

        parser = HTMLParser(self.include_tag, self.exclude_tag)
        parser.feed(outer_html)

        webpage_object = WebPageObject(url=url, metadata=metadata, parser=parser)

        elapsed_time = time.time() - start_time
        logging.info(f"Finished fetching '{url}' in {elapsed_time:.2f}s.")

        return webpage_object

    def fetch_document(self, url: str) -> Document:
        return self.fetch(url).to_document()
