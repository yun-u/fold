from enum import Enum
from typing import Union

import requests
from pydantic import BaseModel, field_serializer, model_validator

from app.utils.pydantic_utils import instance_to_dict

MAX_TRANSLATE_LENGTH = 5000


class Language(Enum):
    KO = "ko"  # 한국어
    EN = "en"  # 영어
    JA = "ja"  # 일본어
    ZH_CN = "zh-CN"  # 중국어 간체
    ZH_TW = "zh-TW"  # 중국어 번체
    VI = "vi"  # 베트남어
    ID = "id"  # 인도네시아어
    TH = "th"  # 태국어
    DE = "de"  # 독일어
    RU = "ru"  # 러시아어
    ES = "es"  # 스페인어
    IT = "it"  # 이탈리아어
    FR = "fr"  # 프랑스어


translations = [
    ("ko", "en"),
    ("en", "ko"),
    ("ko", "ja"),
    ("ja", "ko"),
    ("ko", "zh-CN"),
    ("zh-CN", "ko"),
    ("ko", "zh-TW"),
    ("zh-TW", "ko"),
    ("ko", "vi"),
    ("vi", "ko"),
    ("ko", "id"),
    ("id", "ko"),
    ("ko", "th"),
    ("th", "ko"),
    ("ko", "de"),
    ("de", "ko"),
    ("ko", "ru"),
    ("ru", "ko"),
    ("ko", "es"),
    ("es", "ko"),
    ("ko", "it"),
    ("it", "ko"),
    ("ko", "fr"),
    ("fr", "ko"),
    ("en", "ja"),
    ("ja", "en"),
    ("en", "fr"),
    ("fr", "en"),
    ("en", "zh-CN"),
    ("zh-CN", "en"),
    ("en", "zh-TW"),
    ("zh-TW", "en"),
    ("ja", "zh-CN"),
    ("zh-CN", "ja"),
    ("ja", "zh-TW"),
    ("zh-TW", "ja"),
    ("zh-CN", "zh-TW"),
    ("zh-TW", "zh-CN"),
]


class PapagoException(Exception):
    def __init__(
        self, http_status_code: int, error_code: str, error_message: str
    ) -> None:
        super().__init__(f"{error_code} {error_message}")
        self.http_status_code = http_status_code
        self.error_code = error_code
        self.error_message = error_message


class TranslationRequest(BaseModel):
    source: Language
    target: Language
    text: str

    @field_serializer("source", "target", return_type=str)
    def serialize_language(self, lang: Language, _info) -> str:
        """Serialize the Language enum to its value (a string)."""
        return lang.value

    @model_validator(mode="after")
    def check_translation(self):
        """Validate if the translation is supported based on the source and target languages."""
        assert (
            self.source.value,
            self.target.value,
        ) in translations, f"({self.source.value}, {self.target.value})"
        return self


class TranslationResult(BaseModel):
    srcLangType: Language
    tarLangType: Language
    translatedText: str
    engineType: str


class Translator:
    _PAPAGO_URL = "https://openapi.naver.com/v1/papago/n2mt"

    def __init__(self, client_id: str, client_secret: str) -> None:
        self.client_id = client_id
        self.client_secret = client_secret

    def translate_text(
        self,
        text: str,
        *,
        source_lang: Union[str, Language],
        target_lang: Union[str, Language],
    ) -> TranslationResult:
        """
        Translate the given text from the source language to the target language using the Papago API.

        Args:
            text (`str`): The text to be translated.
            source_lang (`Union[str, Language]`): The source language of the text. Can be a string or Language enum value.
            target_lang (`Union[str, Language]`): The target language for translation. Can be a string or Language enum value.

        Returns:
            `TranslationResponse`: The translated text along with other translation information.

        Raises:
            PapagoException: If there is an error in the translation process.
            HTTPError:  If there is an HTTP error during the API request.
        """
        headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
        }
        param = TranslationRequest(source=source_lang, target=target_lang, text=text)

        response = requests.post(
            self._PAPAGO_URL,
            headers=headers,
            data=instance_to_dict(param),
        )
        if response.status_code == 200:
            return TranslationResult(**response.json()["message"]["result"])
        elif response.status_code == 400:
            raise PapagoException(
                response.status_code, response["errorCode"], response["errorMessage"]
            )
        response.raise_for_status()
