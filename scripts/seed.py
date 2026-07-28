from sqlalchemy.orm import Session
from sqlalchemy import select
import bcrypt

from app.core.database import SessionLocal
from app.models.entities import (
    Bank,
    User,
    Service,
    Counter,
    UserRole,
    CounterStatus,
)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def seed():
    db: Session = SessionLocal()
    try:
        # ===============================
        # BANQUE
        # ===============================
        bank = db.scalar(select(Bank).where(Bank.name == "PA GEN KANPE BANK"))
        if not bank:
            bank = Bank(
                name="PA GEN KANPE BANK",
                branch_name="Agence Principale",
                address="Ouanaminthe, Haiti",
                phone="+50937000000",
            )
            db.add(bank)
            db.commit()
            db.refresh(bank)
            print("✓ Banque créée")
        else:
            print("✓ Banque déjà existante")

        # ===============================
        # SERVICES
        # ===============================
        services = [
            ("DEP", "Dépôt", 5),
            ("RET", "Retrait", 4),
            ("TRF", "Transfert", 8),
            ("INF", "Information", 3),
        ]
        for code, name, minutes in services:
            existing = db.scalar(select(Service).where(Service.code == code))
            if not existing:
                db.add(
                    Service(
                        bank_id=bank.id,
                        code=code,
                        name=name,
                        average_minutes=minutes,
                    )
                )
        db.commit()
        print("✓ Services créés")

        # ===============================
        # ADMIN
        # ===============================
        admin = db.scalar(select(User).where(User.email == "admin@pakanpe.com"))
        if not admin:
            admin = User(
                bank_id=bank.id,
                full_name="Super Administrateur",
                email="admin@pakanpe.com",
                phone="+50930000001",
                password_hash=hash_password("Admin123!"),
                role=UserRole.ADMIN.value,
            )
            db.add(admin)
        print("✓ Admin créé")

        # ===============================
        # AGENT
        # ===============================
        agent = db.scalar(select(User).where(User.email == "agent@pakanpe.com"))
        if not agent:
            agent = User(
                bank_id=bank.id,
                full_name="Agent Principal",
                email="agent@pakanpe.com",
                phone="+50930000002",
                password_hash=hash_password("Agent123!"),
                role=UserRole.AGENT.value,
            )
            db.add(agent)
        print("✓ Agent créé")

        # CAISSIER
        cashier = db.scalar(select(User).where(User.email == "cashier@pakanpe.com"))
        if not cashier:
            cashier = User(
                bank_id=bank.id,
                full_name="Caissier Principal",
                email="cashier@pakanpe.com",
                phone="+50930000003",
                password_hash=hash_password("Cashier123!"),
                role=UserRole.CASHIER.value,
            )
            db.add(cashier)

        # 🔥 Important : COMMIT avant de réutiliser cashier
        db.commit()
        db.refresh(cashier)  # ← Récupère l'ID généré
        print("✓ Caissier créé")

        # ===============================
        # GUICHETS (avec cashier déjà commit)
        # ===============================
        counters = [
            (1, "Guichet 1"),
            (2, "Guichet 2"),
            (3, "Guichet 3"),
        ]

        for number, name in counters:
            exists = db.scalar(
                select(Counter).where(
                    Counter.bank_id == bank.id,
                    Counter.number == number,
                )
            )
            if not exists:
                db.add(
                    Counter(
                        bank_id=bank.id,
                        number=number,
                        name=name,
                        status=CounterStatus.CLOSED.value,
                        cashier_id=cashier.id,  # ← Maintenant cashier.id existe
                    )
                )

        db.commit()
        print("✓ Guichets créés")

        # ===============================
        # RÉSUMÉ FINAL
        # ===============================
        print("\n===================================")
        print("BASE DE DONNÉES INITIALISÉE")
        print("===================================")
        print("📧 Comptes de démonstration :")
        print("  🛡️ Admin   : admin@pakanpe.com / Admin123!")
        print("  🎯 Agent   : agent@pakanpe.com / Agent123!")
        print("  💰 Caissier : cashier@pakanpe.com / Cashier123!")
        print("===================================")

    except Exception as e:
        db.rollback()
        print(f"❌ ERREUR : {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()