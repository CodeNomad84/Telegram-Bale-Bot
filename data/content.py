"""Load all content once at import time; handlers read from these in-memory maps."""

from config import (
    INTRO_FILE,
    PRODUCTS_FILE,
    QUESTIONS_FILE,
    RESULT_IMAGES_FILE,
    RESULT_TEXTS_FILE,
)
from data.loaders import (
    load_intro,
    load_products,
    load_questions,
    load_result_images,
    load_result_texts,
)

INTRO = load_intro(INTRO_FILE)
QUESTIONS = load_questions(QUESTIONS_FILE)
RESULT_TEXTS = load_result_texts(RESULT_TEXTS_FILE)
RESULT_IMAGES = load_result_images(RESULT_IMAGES_FILE)
PRODUCTS = load_products(PRODUCTS_FILE)

# Order in which intro questions are asked. The second one is parents only.
INTRO_ORDER = ["marital", "child_gender"]