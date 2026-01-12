import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

# Add parent directory to path to import backend modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.database.mongo import get_database, MongoDB
from backend.database.mongo_models import SubmissionModel, DocumentModel

async def seed_data():
    print("=" * 60)
    print("SEEDING DATABASE WITH SAMPLE DATA")
    print("=" * 60)
    
    # Initialize connection
    await MongoDB.connect_db()
    db = MongoDB.db
    
    if db is None:
        print("❌ Failed to connect to database.")
        return

    # Clear existing data
    print("Cleaning old data...")
    await db.submissions.delete_many({})
    await db.queries.delete_many({})
    
    stages = ["RAPO", "LITIGATION", "CONTROL"]
    statuses = ["NEW", "IN_PROGRESS", "WAITING_INFO", "COMPLETED"]
    
    samples = [
        {
            "email": "sophie.dubois@example.com",
            "phone": "06 12 34 56 78",
            "description": "Following a logic check, my RSA was suspended without notice. I have 2 children and no other income. I sent the requested documents 2 weeks ago but no response.",
            "doc_name": "Lettre_Suspension_RSA.pdf",
            "prestations": ["RSA", "Allocations Familiales"]
        },
        {
            "email": "marc.legrand@test.org",
            "phone": "07 98 76 54 32",
            "description": "Contestation of APL recalculation. They claim I live with a partner which is false. I live alone since January.",
            "doc_name": "Recalcul_APL_Janvier.pdf",
            "prestations": ["APL"]
        },
        {
            "email": "julie.martin@demo.fr",
            "phone": "01 22 33 44 55",
            "description": "Requesting an appeal for AAH refusal. My disability rate was evaluated at 45% but my doctor says it should be 80%.",
            "doc_name": "Dossier_Medical_MDPH.pdf",
            "prestations": ["AAH"]
        },
        {
            "email": "thomas.bernard@example.net",
            "phone": "06 55 44 33 22",
            "description": "Unjustified debt claim from Pôle Emploi for 2000 euros regarding overpayment in 2023. I contest this amount.",
            "doc_name": "Notification_Trop_Percu.pdf",
            "prestations": ["Chômage"]
        },
        {
             "email": "sophie.dubois@example.com",
             "phone": "06 12 34 56 78",
             "description": "Sending additional proof of address for the RSA file.",
             "doc_name": "Justificatif_Domicile.pdf",
             "prestations": ["RSA"]
        }
    ]
    
    print(f"Inserting {len(samples)} sample cases...")
    
    for i, sample in enumerate(samples):
        # Create timestamps from last 2 weeks
        days_ago = random.randint(0, 14)
        submitted_at = datetime.utcnow() - timedelta(days=days_ago)
        
        # Generate ID
        case_id = f"CAS_{submitted_at.strftime('%d-%m-%y_%H:%M:%S')}"
        
        sub = SubmissionModel(
            case_id=case_id,
            cas_number=i+1,
            email=sample["email"],
            phone=sample["phone"],
            description=sample["description"],
            submitted_at=submitted_at,
            status=random.choice(statuses),
            stage=random.choice(stages),
            prestations_detected=sample.get("prestations", []),
            generated_email_draft=f"Dear {sample['email']},\n\nWe acknowledge receipt of your document regarding {sample['doc_name']}.\n\nSincerely,\nLegal Team",
            generated_appeal_draft=f"To the Appeals Board,\n\nWe hereby contest the decision regarding {sample['email']}...\n\nGrounds for appeal:\n- {sample['description']}",
            document=DocumentModel(
                filename=sample["doc_name"], 
                mime_type="application/pdf"
            )
        )
        
        # Insert
        sub_dict = sub.model_dump(by_alias=True, exclude_none=True)
        await db.submissions.insert_one(sub_dict)
        print(f"  ✓ Inserted: {case_id} ({sample['email']})")

    print("\n✅ Database seeded successfully!")
    print("Refresh your browser to see the data.")
    
    # Close connection
    await MongoDB.close_db()

if __name__ == "__main__":
    asyncio.run(seed_data())
