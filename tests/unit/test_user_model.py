import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from app.models import User, UserRole, Bank
from app.core.security import hash_password

pytestmark = pytest.mark.unit


def test_prevent_duplicate_email(db_session):
    """Vérifie que la BDD bloque la création de deux utilisateurs avec le même email."""
    # Récupération de l'id de la banque créée par le seeding
    bank = db_session.scalar(select(Bank))

    user1 = User(
        bank_id=bank.id,
        full_name="Alice Test",
        email="duplicata@ong.org",
        phone="+50930000099",
        password_hash=hash_password("Password123!"),
        role=UserRole.AGENT.value,
    )
    user2 = User(
        bank_id=bank.id,
        full_name="Bob Test",
        email="duplicata@ong.org",  #Même email !
        phone="+50930000098",
        password_hash=hash_password("Password123!"),
        role=UserRole.AGENT.value,
    )

    db_session.add(user1)
    db_session.commit()

    db_session.add(user2)
    with pytest.raises(IntegrityError):  #La BDD doit lever cette erreur Postgres/SQLite
        db_session.commit()