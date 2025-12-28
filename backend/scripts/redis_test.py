import redis
import sys
import os 

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.schemas.messages import Status, ScrapeUpdateMessage
from app.core.config import settings

def test_redis_1():
    testing_output = ScrapeUpdateMessage(task_id="testing_#1", status=Status.COMPLETED.value, jobs_found=67)
    
    r = redis.from_url(settings.redis_url)
    r.publish(settings.scrape_update_chanel, testing_output.model_dump_json())


def test_redis_2():
    testing_output = ScrapeUpdateMessage(task_id="testing_#2", status=Status.COMPLETED.value, jobs_found=20)
    
    r = redis.from_url(settings.redis_url)
    r.publish(settings.scrape_update_chanel, testing_output.model_dump_json())
    
    
def main():
    test_redis_1()
    test_redis_2()
    return 0 
    
if __name__ == "__main__":
    sys.exit(main())