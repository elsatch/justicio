import os
import typing as tp
import logging as lg

from requests.exceptions import HTTPError
# from qdrant_client.http.models import Filter, FieldCondition, MatchValue
# from qdrant_client import QdrantClient
import numpy as np

from src.email.send_email import send_email
from src.etls.boe.scrapper import BOEScrapper
from src.etls.boe.loading.defs_id_largos import BOE_IDS
from src.etls.common.etl import ETL
from src.etls.boe.defs import COLLECTION_NAME
from src.initialize import initialize_app, initialize_logging

initialize_logging()

# QDRANT_CLIENT = QdrantClient(url=os.environ["QDRANT_API_URL"], api_key=os.environ["QDRANT_API_KEY"], timeout=1000)


def load_important_ids(filename):
    with open(filename) as f:
        lines = f.read().splitlines()
    return lines


def filter_documents_by_year(documents: tp.List[str]) -> tp.List[str]:
    documents_filtered = []
    for document_id in documents:
        id_split = document_id.split("-")
        if id_split[0] != "BOE" or int(id_split[2]) < 2000:
            documents_filtered.append(document_id)
    return documents_filtered

if __name__ == "__main__":
    logger = lg.getLogger("__main__")
    INIT_OBJECTS = initialize_app()
    # etl_job = ETL(config_loader=INIT_OBJECTS.config_loader, vector_store=INIT_OBJECTS.vector_store[COLLECTION_NAME])
    boe_scrapper = BOEScrapper()

    documents = load_important_ids("src/etls/boe/loading/defs_ids_importantes.txt")
    documents += BOE_IDS
    logger.info("Documents size: %s", len(documents))
    documents_filtered = list(set(documents))
    logger.info("Documents filtered by unique: %s", len(documents_filtered))
    documents_filtered = filter_documents_by_year(documents_filtered)
    logger.info("Documents filtered by year: %s", len(documents_filtered))
    logger.info(documents_filtered)
    # documents_filtered = filter_documents_loaded(documents_filtered)
    # logger.info('Documents filtered size: %s', len(documents_filtered))

    docs = []
    for boe_id in documents_filtered:
        logger.info("Loading BOE Id: %s", boe_id)
        url = f"https://www.boe.es/diario_boe/xml.php?id={boe_id}"
        try:
            meta_document = boe_scrapper.download_document(url)
            docs.append(meta_document)
        except HTTPError:
            logger.error("Not scrapped document %s", url)
        except AttributeError:
            logger.error("Not scrapped document %s", url)
        # if docs:
        #    etl_job.run(docs)

    # Save documents to XML in the test folder
            
    if not os.path.exists("test"):
        os.makedirs("test")

    for doc in docs:
        with open(f"test/{doc['id']}.xml", "w") as f:
            f.write(doc["xml"])
    
    
            

    subject = "[BOE] Documents ETL executed"
    content = f"""
    Documents ETL executed
    - Documents loaded (BOE ids): {len(documents_filtered)}
    - Documents downloaded loaded: {len(docs)}
    """
    # send_email(INIT_OBJECTS.config_loader, subject, content)