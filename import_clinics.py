import csv
from main import app
from database import db
from models import Clinic

def import_clinics_from_csv(csv_file='indian_ivf_clinics.csv'):
    with app.app_context():
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            clinics_added = 0
            for row in reader:
                # Check if clinic already exists by name
                existing_clinic = Clinic.query.filter_by(name=row['Clinic Name']).first()
                if existing_clinic:
                    print(f"Clinic '{row['Clinic Name']}' already exists, skipping.")
                    continue

                # Create new clinic
                clinic = Clinic(
                    name=row['Clinic Name'],
                    address=row['Address'],
                    city=row['City'],
                    state=row['State'],
                    phone=row['Phone'],
                    website=row['Website'],
                    description=row['Description']
                )
                db.session.add(clinic)
                clinics_added += 1
                print(f"Added clinic: {row['Clinic Name']}")

            db.session.commit()
            print(f"Successfully imported {clinics_added} clinics from {csv_file}")

if __name__ == "__main__":
    import_clinics_from_csv()
