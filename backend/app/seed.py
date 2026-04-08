from app.database import SessionLocal, engine, Base
from app.models.hcp import HCP


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    if db.query(HCP).count() > 0:
        print("Database already seeded.")
        db.close()
        return

    hcps = [
        HCP(full_name="Dr. Smith", specialty="Cardiology", organization="City Heart Hospital"),
        HCP(full_name="Dr. Sharma", specialty="Oncology", organization="Cancer Care Institute"),
        HCP(full_name="Dr. Patel", specialty="Neurology", organization="Brain & Spine Clinic"),
        HCP(full_name="Dr. Johnson", specialty="Endocrinology", organization="Metro Diabetes Center"),
        HCP(full_name="Dr. Williams", specialty="Pulmonology", organization="Lung Health Center"),
        HCP(full_name="Dr. Brown", specialty="Dermatology", organization="Skin Care Clinic"),
        HCP(full_name="Dr. Davis", specialty="Pediatrics", organization="Children's Hospital"),
        HCP(full_name="Dr. Wilson", specialty="Gastroenterology", organization="GI Associates"),
    ]

    db.add_all(hcps)
    db.commit()
    print(f"Seeded {len(hcps)} HCPs.")
    db.close()


if __name__ == "__main__":
    seed()
