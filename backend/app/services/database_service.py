from supabase import create_client, Client
from typing import Optional

from app.core.config import settings
from app.schemas.database_tables import Job, Preference

supabase: Client = create_client(settings.supabase_url, settings.supabase_key)

# ============================================================
# JOBS
# ============================================================

def get_jobs(user_id: str) -> Optional[list[Job]]:
    # Returns all jobs from a user, date descending
    # Used by frontend for displaying all jobs
    
    result = supabase.table("jobs") \
        .select("*") \
            .eq("user_id",user_id) \
                .order("scraped_at", desc=True) \
                    .execute()
    
    if not result.data:
        return None
    
    job_listings = [Job(**listing) for listing in result.data()]
        
    return job_listings

def delete_job_by_id(user_id: str, job_id: str):
    # Deletes one job listing from a user by id
    # Used by frontend for removing jobs

    supabase.table("jobs") \
        .delete() \
            .eq("user_id",user_id) \
                .eq("id",job_id) \
                    .execute()
    
def create_job(user_id: str, job_data: Job):
    # Adds one job to the database for user
    job = {'user_id': user_id, **job_data.model_dump(exclude={'id'})}
    print(f"\nInserting job: {job}")  
    result = supabase.table('jobs').insert(job).execute()
    print(f"\nResult: {result}")  
# ============================================================
# Preferences
# ============================================================

def get_preferences(user_id: str) -> Optional[Preference]:
    # Gets user preferences
    # Used by frontend when displaying preferences
    
    result = supabase.table('preferences') \
        .select('*').eq('user_id', user_id).execute()
    
    if not result.data:
        return None
    
    
    return Preference(**result.data[0]) 

def update_preference(user_id: str, update: Preference):
    # Updates user preferences
    # Used by frontend when altering preferences
    
    supabase.table('preferences') \
        .update(update.model_dump()) \
            .eq('user_id', user_id) \
                .execute()
                
# ============================================================
# User Data
# ============================================================

def get_user_email(user_id: str) -> Optional[str]:
    # Gets user's email from supabase
    # Used by backend once scrape completes
    
    try:
        result = supabase.auth.admin.get_user_by_id(user_id)
        return result.user.email if result.user else None
    except Exception as e:
        print(f'Failed to get user email: {e}')
        return None