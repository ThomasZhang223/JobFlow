from supabase import create_client, Client
from typing import Optional

from app.core.config import settings
from app.schemas.database_tables import Job, Preference, Statistics

supabase: Client = create_client(settings.supabase_url, settings.supabase_key)

# ============================================================
# JOBS
# ============================================================

def get_jobs(user_id: str) -> Optional[list[Job]]:
    # Returns all jobs from a user, priority first then title ascending
    # Used by frontend for displaying all jobs

    try:
        result = supabase.table("jobs") \
            .select("*") \
                .eq("user_id", user_id) \
                    .order("priority", desc=True) \
                    .order("title", desc=False) \
                        .execute()

        if not result.data:
            return None

        job_listings = [Job(**listing) for listing in result.data]

        return job_listings
    except Exception as e:
        print(f"Error in get_jobs: {e}")
        print(f"User ID: {user_id}")
        if 'result' in locals():
            print(f"Result: {result}")
        raise

def get_job_by_id(user_id: str, job_id: int) -> Job:
    # Gets one job listing from a user by id
    # Used by frontend for seeing job details

    result = supabase.table("jobs") \
        .select('*') \
            .eq("user_id",user_id) \
                .eq("id",job_id) \
                    .execute()

    if not result.data:
        raise ValueError(f"Job with id {job_id} not found for user {user_id}")

    return Job(**result.data[0])
            
def delete_job_by_id(user_id: str, job_id: int):
    # Deletes one job listing from a user by id
    # Used by frontend for removing jobs

    supabase.table("jobs") \
        .delete() \
            .eq("user_id",user_id) \
                .eq("id",job_id) \
                    .execute()

def toggle_job_priority(user_id: str, job_id: int) -> bool:
    # Toggles the priority status of a job (True <-> False)
    # Used by frontend for marking jobs as priority

    # First get current priority status
    result = supabase.table("jobs") \
        .select("priority") \
            .eq("user_id", user_id) \
                .eq("id", job_id) \
                    .execute()

    if not result.data:
        return False  # Job not found

    # Toggle the priority value
    current_priority = result.data[0].get("priority")
    new_priority = not current_priority

    # Update the job with new priority
    supabase.table("jobs") \
        .update({"priority": new_priority}) \
            .eq("user_id", user_id) \
                .eq("id", job_id) \
                    .execute()

    return True

def get_priority_jobs(user_id: str) -> Optional[list[Job]]:
    # Returns only priority jobs from a user, title ascending
    # Used by frontend for displaying priority jobs only

    result = supabase.table("jobs") \
        .select("*") \
            .eq("user_id", user_id) \
            .eq("priority", True) \
                .order("title", desc=False) \
                    .execute()

    if not result.data:
        return None

    job_listings = [Job(**listing) for listing in result.data]

    return job_listings

def search_jobs(user_id: str, query: str) -> Optional[list[Job]]:
    # Search jobs by title, company_name, location, job_type, salary, or benefits
    # Used by frontend search bar

    if not query or not query.strip():
        return None

    search_term = f"%{query.strip().lower()}%"

    result = supabase.table("jobs") \
        .select("*") \
            .eq("user_id", user_id) \
            .or_(f"title.ilike.{search_term},company_name.ilike.{search_term},location.ilike.{search_term},job_type.ilike.{search_term},salary.ilike.{search_term},benefits.ilike.{search_term}") \
                .order("priority", desc=True) \
                .order("title", desc=False) \
                    .execute()

    if not result.data:
        return None

    job_listings = [Job(**listing) for listing in result.data]

    return job_listings

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
    
def update_completed(user_id: str, job_id: int):
    # Increments user's completed jobs by one then deletes the listing
    # Used by frontend to mark complete
    
    current = supabase.table('user_statistics').select('*').eq('user_id', user_id).execute()
    if current.data:
        stats = current.data[0]
        stats['current_jobs'] -= 1
        stats['completed_jobs'] += 1

        listing = get_job_by_id(user_id, job_id)
        if listing.priority:
            stats['saved_jobs'] -= 1

        delete_job_by_id(user_id, job_id)
        supabase.table('user_statistics').update(stats).eq('user_id', user_id).execute()
    else:
        # No user statistics found, still delete the job but can't update stats
        delete_job_by_id(user_id, job_id)
    
def get_user_statistics(user_id: str) -> Optional[Statistics]:
    # Gets user statistics
    # Used by frontend to display dashboard

    result = supabase.table('user_statistics') \
        .select('*').eq('user_id', user_id).execute()

    if not result.data:
        return None

    return Statistics(**result.data[0]) 