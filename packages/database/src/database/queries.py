from sqlalchemy import select, and_
from database.models import BookEntry, LabelEntry


def get_unlabeled_book_images(session, target_sellers: list[str] | None) -> list[str]:
    """
    Returns a list of image URLs for books that are unlabeled."""

    entries = (
        select(BookEntry.image_url)
        .outerjoin(LabelEntry, BookEntry.image_url == LabelEntry.image_url)
        .where(
            and_(
                LabelEntry.image_url == None,
                BookEntry.magazine == False,
                BookEntry.seller_id.in_(target_sellers) if target_sellers else True,
            ),
        )
        .order_by(BookEntry.sold_date.desc(), BookEntry.listingid.desc())
    )
    unlabeled_images = session.scalars(entries).all()
    return unlabeled_images


if __name__ == "__main__":
    from database.main import get_session

    session = get_session()
    urls = get_unlabeled_book_images(session, target_sellers=["sinja_japan_shop"])
    print(urls)
