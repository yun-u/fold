import logging
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, List, Tuple

import transformers

from app.detect_language import Language, detect_language
from app.embedding_pipeline.papago import MAX_TRANSLATE_LENGTH, Translator
from app.secrets import secrets

SPLIT_PATTERN = re.compile(
    r"((?<!(et al))(?# e.g. et al.)(?<! [A-Z])(?# e.g. John F. Kennedy)\.\s+|\.\s*$)"
)
MAX_LENGTH = 8192


def clean_text(text: str) -> str:
    # change confusing unicode
    text = re.sub(r"\u00b4", "`", text)  # ´ -> `
    text = re.sub(r"\u201c|\u201d|\u201e", '"', text)  # “,”,„ -> "
    text = re.sub(r"\u2018|\u2019|\u02bb|\u02bc|\u02c8", "'", text)  # ‘,’,ʻ,ʼ,ˈ -> '

    # hyphenation
    text = re.sub(r"-\n", "", text)

    text = re.sub(r"\s+", " ", text)
    return text


def split_text_by_full_stop(text: str) -> List[str]:
    """
    Splits a given text into sentences based on a more comprehensive full-stop pattern.

    Args:
        text (`str`): The input text to be split into sentences.

    Returns:
        `List[str]`: A list of sentences extracted from the input text.
    """
    texts = []
    i = 0
    for m in SPLIT_PATTERN.finditer(text):
        pos, endpos = m.span()
        texts.append(text[i:pos] + ".")
        i = endpos

    # handle the last sentence if it's incomplete
    if i < len(text):
        texts.append(text[i:])

    return texts


def split_text_by_condition(
    text: str,
    condition_function: Callable[[str], int],
    condition_value: int,
) -> List[str]:
    texts = split_text_by_full_stop(text)

    indexes, start_index, value, i = [], 0, 0, 0
    for i, t in enumerate(texts):
        current_value = condition_function(t)
        value += current_value

        if i > 0 and value > condition_value:
            indexes.append([start_index, i - 1])  # not include i
            start_index, value = i, current_value
    indexes.append([start_index, i])

    return [" ".join(texts[start : end + 1]) for (start, end) in indexes]


def split_text_by_tokenizer(
    text: str, tokenizer: transformers.PreTrainedTokenizerBase
) -> List[str]:
    def token_length(t):
        return len(tokenizer.tokenize(t))

    max_len_single_sentence = min(
        MAX_LENGTH - tokenizer.num_special_tokens_to_add(),
        tokenizer.max_len_single_sentence,
    )

    return split_text_by_condition(text, token_length, max_len_single_sentence)


def split_text_by_bytesize(text: str, max_bytesize: int) -> List[str]:
    def byte_size(t):
        return len(t.encode("utf-8"))

    return split_text_by_condition(text, byte_size, max_bytesize)


def split_text_by_length(text: str, max_length: int) -> List[str]:
    def text_length(t):
        return len(t)

    return split_text_by_condition(text, text_length, max_length)


def translate_text(text: str) -> str:
    translator = Translator(secrets.papago.client_id, secrets.papago.client_secret)

    texts = split_text_by_length(text, MAX_TRANSLATE_LENGTH)
    langs = detect_language(texts)

    def fn(args: Tuple[str, Language]) -> str:
        text_, lang = args

        if lang == Language.EN:
            return text_
        elif lang == Language.KO:
            result = translator.translate_text(
                text_, source_lang=lang.value, target_lang="en"
            )
            logging.info(f"Translate {lang} text: {text_} -> {result.translatedText}")
            return result.translatedText
        else:
            # TODO: only translate KO?
            return text_

    with ThreadPoolExecutor(max_workers=None) as executor:
        translated_texts = executor.map(fn, zip(texts, langs))

    return " ".join(translated_texts)


def preprocess_text(
    text: str, tokenizer: transformers.PreTrainedTokenizerBase
) -> List[str]:
    text = clean_text(text)
    text = translate_text(text)
    return split_text_by_tokenizer(text, tokenizer)
