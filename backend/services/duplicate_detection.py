"""Duplicate detection service using rapidfuzz."""
from rapidfuzz import fuzz
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.database.models import Submission
from typing import Optional

class DuplicateDetectionService:
    """Service for detecting duplicate submissions."""
    
    # Threshold for considering submissions as duplicates
    SIMILARITY_THRESHOLD = 85  # 85% similarity
    
    @staticmethod
    async def find_duplicate(
        email: str,
        phone: str,
        db: AsyncSession
    ) -> Optional[Submission]:
        """Find duplicate submission using fuzzy matching."""
        # Get all existing submissions
        result = await db.execute(select(Submission))
        existing_submissions = result.scalars().all()
        
        for submission in existing_submissions:
            # Calculate similarity scores
            email_similarity = fuzz.ratio(email.lower(), submission.email.lower())
            phone_similarity = fuzz.ratio(phone, submission.phone)
            
            # Combined similarity (weighted average)
            combined_similarity = (email_similarity * 0.6) + (phone_similarity * 0.4)
            
            if combined_similarity >= DuplicateDetectionService.SIMILARITY_THRESHOLD:
                return submission
        
        return None
    
    @staticmethod
    async def replace_submission(
        old_submission: Submission,
        new_data: dict,
        db: AsyncSession
    ) -> Submission:
        """Replace existing submission with new data."""
        # Update fields
        old_submission.email = new_data.get('email', old_submission.email)
        old_submission.phone = new_data.get('phone', old_submission.phone)
        old_submission.description = new_data.get('description', old_submission.description)
        old_submission.submitted_at = new_data.get('submitted_at', old_submission.submitted_at)
        
        # Delete old documents (they will be re-processed)
        # This is handled by cascade delete in the relationship
        
        await db.commit()
        await db.refresh(old_submission)
        
        return old_submission

