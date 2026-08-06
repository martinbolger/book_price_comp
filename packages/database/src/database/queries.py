from sqlalchemy import or_, select, and_
from database.models import BookEntry, LabelEntry
from database.main import get_session


def get_unlabeled_book_images(
    model_used: str, target_sellers: list[str] | None, session=None
) -> list[str]:
    """Returns a list of image URLs for books that are unlabeled."""

    # Get database session if one was not provided
    if session is None:
        session = get_session()

    # Filter to only the target sellers if provided, otherwise, include all sellers
    # Use an outer join on the image_url to find books that are not yet labeled
    entries = (
        select(BookEntry.image_url)
        .outerjoin(LabelEntry, BookEntry.image_url == LabelEntry.image_url)
        .where(
            and_(
                or_(LabelEntry.image_url == None, LabelEntry.model_used != model_used),
                BookEntry.magazine.is_not(True),
                BookEntry.seller_id.in_(target_sellers) if target_sellers else True,
            ),
        )
        .order_by(BookEntry.sold_date.desc(), BookEntry.listingid.desc())
    )
    unlabeled_images = session.scalars(entries).all()
    return unlabeled_images
