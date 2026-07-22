from sqlalchemy import select

from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models import Bank, Counter, CounterStatus, Service, User, UserRole


def seed() -> None:
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        bank = db.scalar(select(Bank).where(Bank.name == "UNIBANK"))
        if bank is None:
            bank = Bank(name="UNIBANK", branch_name="Agence principale")
            db.add(bank)
            db.flush()

        service_rows = [
            ("DEPOT", "Dépôt d'argent", 4),
            ("RETRAIT", "Retrait d'argent", 5),
            ("COMPTE", "Ouverture de compte", 12),
            ("AUTRE", "Autre service", 7),
        ]
        for code, name, minutes in service_rows:
            if db.scalar(select(Service.id).where(Service.code == code)) is None:
                db.add(
                    Service(
                        bank_id=bank.id,
                        code=code,
                        name=name,
                        average_minutes=minutes,
                    )
                )

        demo_users = [
            (
                "Administrateur Démo",
                "admin@pagenkanpe.ht",
                "+50937000001",
                "Admin123!",
                UserRole.ADMIN,
            ),
            ("Agent Démo", "agent@pagenkanpe.ht", "+50937000002", "Agent123!", UserRole.AGENT),
            (
                "Caissier Démo",
                "cashier@pagenkanpe.ht",
                "+50937000003",
                "Cashier123!",
                UserRole.CASHIER,
            ),
        ]
        for name, email, phone, password, role in demo_users:
            if db.scalar(select(User.id).where(User.email == email)) is None:
                db.add(
                    User(
                        bank_id=bank.id,
                        full_name=name,
                        email=email,
                        phone=phone,
                        password_hash=hash_password(password),
                        role=role.value,
                    )
                )

        if db.scalar(select(Counter.id).limit(1)) is None:
            for number in range(1, 4):
                db.add(
                    Counter(
                        bank_id=bank.id,
                        number=number,
                        name=f"Guichet {number}",
                        status=CounterStatus.CLOSED.value,
                    )
                )
        db.commit()


if __name__ == "__main__":
    seed()
