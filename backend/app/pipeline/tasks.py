import itertools as it
import queue
from typing import List

from celery import group

from app.utils.ordered_set import OrderedSet

from .fetch.tasks import fetch_and_embed


def process(url: str, model_id: str) -> List[str]:
    def squeeze(q: queue.Queue) -> List:
        items = []
        while not q.empty():
            items.append(q.get_nowait())
        return items

    total = OrderedSet([url])

    q = queue.Queue()
    q.put_nowait(url)

    while not q.empty():
        res = group([fetch_and_embed.s(u, model_id) for u in squeeze(q)])()
        for u in it.chain.from_iterable(res.get()):
            # to prevent circular references
            if u in total:
                continue

            q.put_nowait(u)
            total.add([u])

    return list(total)
