import logging
from enum import Enum
from pathlib import Path
from typing import List, Union

from fasttext.FastText import _FastText

MODEL_PATH = Path(__file__).parent / "lid.176.ftz"


model: _FastText = None


class Language(Enum):
    AF = "af"  # Afrikaans
    ALS = "als"  # Alemannic
    AM = "am"  # Amharic
    AN = "an"  # Aragonese
    AR = "ar"  # Arabic
    ARZ = "arz"  # Egyptian Arabic
    AS = "as"  # Assamese
    AST = "ast"  # Asturian
    AV = "av"  # Avar
    AZ = "az"  # Azerbaijani
    AZB = "azb"  # South Azerbaijani
    BA = "ba"  # Bashkir
    BAR = "bar"  # Bavarian
    BCL = "bcl"  # Central Bicolano
    BE = "be"  # Belarusian
    BG = "bg"  # Bulgarian
    BH = "bh"  # Bihari
    BN = "bn"  # Bengali
    BO = "bo"  # Tibetan
    BPY = "bpy"  # Bishnupriya Manipuri
    BR = "br"  # Breton
    BS = "bs"  # Bosnian
    BXR = "bxr"  # Buryat
    CA = "ca"  # Catalan
    CBK = "cbk"  # Chavacano
    CE = "ce"  # Chechen
    CEB = "ceb"  # Cebuano
    CKB = "ckb"  # Sorani Kurdish
    CO = "co"  # Corsican
    CS = "cs"  # Czech
    CV = "cv"  # Chuvash
    CY = "cy"  # Welsh
    DA = "da"  # Danish
    DE = "de"  # German
    DIQ = "diq"  # Zazaki
    DSB = "dsb"  # Lower Sorbian
    DTY = "dty"  # Doteli
    DV = "dv"  # Dhivehi
    EL = "el"  # Greek
    EML = "eml"  # Emiliano-Romagnolo
    EN = "en"  # English
    EO = "eo"  # Esperanto
    ES = "es"  # Spanish
    ET = "et"  # Estonian
    EU = "eu"  # Basque
    FA = "fa"  # Persian
    FI = "fi"  # Finnish
    FR = "fr"  # French
    FRR = "frr"  # Northern Frisian
    FY = "fy"  # Western Frisian
    GA = "ga"  # Irish
    GD = "gd"  # Scottish Gaelic
    GL = "gl"  # Galician
    GN = "gn"  # Guarani
    GOM = "gom"  # Goan Konkani
    GU = "gu"  # Gujarati
    GV = "gv"  # Manx
    HE = "he"  # Hebrew
    HI = "hi"  # Hindi
    HIF = "hif"  # Fiji Hindi
    HR = "hr"  # Croatian
    HSB = "hsb"  # Upper Sorbian
    HT = "ht"  # Haitian Creole
    HU = "hu"  # Hungarian
    HY = "hy"  # Armenian
    IA = "ia"  # Interlingua
    ID = "id"  # Indonesian
    IE = "ie"  # Interlingue
    ILO = "ilo"  # Ilokano
    IO = "io"  # Ido
    IS = "is"  # Icelandic
    IT = "it"  # Italian
    JA = "ja"  # Japanese
    JBO = "jbo"  # Lojban
    JV = "jv"  # Javanese
    KA = "ka"  # Georgian
    KK = "kk"  # Kazakh
    KM = "km"  # Khmer
    KN = "kn"  # Kannada
    KO = "ko"  # Korean
    KRC = "krc"  # Karachay-Balkar
    KU = "ku"  # Kurdish
    KV = "kv"  # Komi
    KW = "kw"  # Cornish
    KY = "ky"  # Kyrgyz
    LA = "la"  # Latin
    LB = "lb"  # Luxembourgish
    LEZ = "lez"  # Lezgian
    LI = "li"  # Limburgish
    LMO = "lmo"  # Lombard
    LO = "lo"  # Lao
    LRC = "lrc"  # Northern Luri
    LT = "lt"  # Lithuanian
    LV = "lv"  # Latvian
    MAI = "mai"  # Maithili
    MG = "mg"  # Malagasy
    MHR = "mhr"  # Eastern Mari
    MIN = "min"  # Minangkabau
    MK = "mk"  # Macedonian
    ML = "ml"  # Malayalam
    MN = "mn"  # Mongolian
    MR = "mr"  # Marathi
    MRJ = "mrj"  # Hill Mari
    MS = "ms"  # Malay
    MT = "mt"  # Maltese
    MWL = "mwl"  # Mirandese
    MY = "my"  # Burmese
    MYV = "myv"  # Erzya
    MZN = "mzn"  # Mazanderani
    NAH = "nah"  # Nahuatl
    NAP = "nap"  # Neapolitan
    NDS = "nds"  # Low German
    NE = "ne"  # Nepali
    NEW = "new"  # Newar
    NL = "nl"  # Dutch
    NN = "nn"  # Norwegian Nynorsk
    NO = "no"  # Norwegian
    OC = "oc"  # Occitan
    OR = "or"  # Odia
    OS = "os"  # Ossetian
    PA = "pa"  # Punjabi
    PAM = "pam"  # Kapampangan
    PFL = "pfl"  # Palatine German
    PL = "pl"  # Polish
    PMS = "pms"  # Piedmontese
    PNB = "pnb"  # Western Punjabi
    PS = "ps"  # Pashto
    PT = "pt"  # Portuguese
    QU = "qu"  # Quechua
    RM = "rm"  # Romansh
    RO = "ro"  # Romanian
    RU = "ru"  # Russian
    RUE = "rue"  # Rusyn
    SA = "sa"  # Sanskrit
    SAH = "sah"  # Sakha
    SC = "sc"  # Sardinian
    SCN = "scn"  # Sicilian
    SCO = "sco"  # Scots
    SD = "sd"  # Sindhi
    SH = "sh"  # Serbo-Croatian
    SI = "si"  # Sinhala
    SK = "sk"  # Slovak
    SL = "sl"  # Slovenian
    SO = "so"  # Somali
    SQ = "sq"  # Albanian
    SR = "sr"  # Serbian
    SU = "su"  # Sundanese
    SV = "sv"  # Swedish
    SW = "sw"  # Swahili
    TA = "ta"  # Tamil
    TE = "te"  # Telugu
    TG = "tg"  # Tajik
    TH = "th"  # Thai
    TK = "tk"  # Turkmen
    TL = "tl"  # Tagalog
    TR = "tr"  # Turkish
    TT = "tt"  # Tatar
    TYV = "tyv"  # Tuvan
    UG = "ug"  # Uighur
    UK = "uk"  # Ukrainian
    UR = "ur"  # Urdu
    UZ = "uz"  # Uzbek
    VEC = "vec"  # Venetian
    VEP = "vep"  # Veps
    VI = "vi"  # Vietnamese
    VLS = "vls"  # West Flemish
    VO = "vo"  # Volapük
    WA = "wa"  # Walloon
    WAR = "war"  # Waray
    WUU = "wuu"  # Wu
    XAL = "xal"  # Kalmyk
    XMF = "xmf"  # Mingrelian
    YI = "yi"  # Yiddish
    YO = "yo"  # Yoruba
    YUE = "yue"  # Cantonese
    ZH = "zh"  # Chinese


def detect_language(text: Union[str, List[str]]) -> List[Language]:
    """Detect the language of the given text using a pre-trained fastText language detection model.

    Args:
        text (`Union[str, List[str]]`): A single text string or a list of text strings to detect the language for.

    Returns:
        `List[Language]`: A list of detected languages corresponding to the input text(s).
    """
    global model

    if model is None:
        logging.info(f"Loading FastText model: {MODEL_PATH.name}")
        model = _FastText(str(MODEL_PATH))

    if isinstance(text, str):
        text = [text]

    labels, _ = model.predict(text, k=1)
    labels: List[List[str]]
    return [Language(label[0][len("__label__") :]) for label in labels]
