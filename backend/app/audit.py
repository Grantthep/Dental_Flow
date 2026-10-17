from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.models import AuditLog


def audit(db: Session, user_id: int | None, action: str, entity_type: str, entity_id: int,
          before: dict | None = None, after: dict | None = None) -> None:
    """Add an audit row in the caller's transaction (committed together with the change)."""
    db.add(AuditLog(
        user_id=user_id, action=action, entity_type=entity_type, entity_id=entity_id,
        changes=jsonable_encoder({"before": before, "after": after}),
    ))
