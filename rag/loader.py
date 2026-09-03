"""Load books from the MySQL database for indexing."""

from langchain_core.documents import Document

from rag.config import BOOK_TEXT_TEMPLATE
from tools.book import get_all_books


def load_books() -> list[Document]:
    """Load every non-deleted book as a Document."""
    docs = []
    for b in get_all_books.invoke({}):
        text = BOOK_TEXT_TEMPLATE.format(
            name=b.get("book_name") or "",
            author=b.get("book_author") or "",
            category=b.get("book_cat") or "",
            genre=b.get("book_genre") or "",
            edition=b.get("edition") or "",
            publication=b.get("publication") or "",
        )
        docs.append(
            Document(
                page_content=text,
                metadata={
                    "doc_type": "book",
                    "book_id": b.get("book_id") or "",
                    "name": b.get("book_name") or "",
                    "author": b.get("book_author") or "",
                    "category": b.get("book_cat") or "",
                    "genre": b.get("book_genre") or "",
                    "row_num": b.get("row_num"),
                },
            )
        )
    return docs
