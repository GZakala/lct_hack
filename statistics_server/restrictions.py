import json
import os

from pathlib import Path
from psql_client import PSQLClient

CUR_DIR = Path(__file__).parent.parent 
    
def restriction_client(entity_id: str
    ) -> str | None:
    restriction_message = PSQLClient(host = os.getenv("RESTRICTIONS_HOST"),
                                     port = os.getenv("RESTRICTIONS_PORT"), 
                                     user = os.getenv("RESTRICTIONS_USER"), 
                                     password = os.getenv("RESTRICTIONS_PASSWORD"), 
                                     dbname = os.getenv("RESTRICTIONS_DBNAME")).select(
                                    f"select restrictions from public.restrictions r where entity_id = '{entity_id}';"
                                    ) 

    if len(restriction_message) > 0:
        result_message = '\n'.join([row['restrictions'] for row in restriction_message])
        return result_message
