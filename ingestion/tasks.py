import asyncio
import logging
from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from atproto import FirehoseSubscribeReposClient, parse_subscribe_repos_message
from django.utils import timezone
from ingestion.models import Event
from tenacity import retry, stop_after_attempt, wait_exponential

# Set up logging
logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def start_firehose_ingestion(self):
    """
    Start ingesting data from the ATProto firehose.
    Includes retry logic and error handling.
    """
    try:
        client = FirehoseSubscribeReposClient()
        
        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=4, max=10),
            reraise=True
        )
        def process_message(message):
            try:
                commit = parse_subscribe_repos_message(message)
                
                # Extract repository information
                repo_name = getattr(commit, 'repo', 'unknown')
                
                # Process operations
                if not hasattr(commit, 'ops') or not commit.ops:
                    logger.warning(f"No operations found in commit for repo: {repo_name}")
                    return

                for op in commit.ops:
                    # Extract operation details
                    action = getattr(op, 'action', 'unknown')
                    record_data = {}
                    
                    # Process the record based on operation type
                    if hasattr(op, 'record'):
                        record_data = {
                            'type': getattr(op.record, '$type', None),
                            'text': getattr(op.record, 'text', None),
                            'created_at': getattr(op.record, 'createdAt', None),
                            'reply_parent': getattr(op.record, 'reply', {}).get('parent', None),
                            'reply_root': getattr(op.record, 'reply', {}).get('root', None),
                            'embed': getattr(op.record, 'embed', None),
                            'langs': getattr(op.record, 'langs', []),
                            'labels': getattr(op.record, 'labels', []),
                        }
                    
                    # Create event record
                    Event.objects.create(
                        repo=repo_name,
                        action=action,
                        record=record_data,
                        created_at=timezone.now()
                    )
                    
                    logger.info(f"Processed {action} event for repo: {repo_name}")
                
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}", exc_info=True)
                raise  # Re-raise for retry mechanism

        def on_message_handler(message):
            try:
                process_message(message)
            except Exception as e:
                logger.error(f"Failed to process message after retries: {str(e)}", exc_info=True)

        def on_connect():
            logger.info("Connected to ATProto firehose")

        def on_disconnect():
            logger.warning("Disconnected from ATProto firehose")

        # Start the client with handlers
        logger.info("Starting firehose ingestion")
        client.start(
            on_message_handler,
            on_connect=on_connect,
            on_disconnect=on_disconnect
        )

    except Exception as exc:
        logger.error(f"Firehose ingestion failed: {str(exc)}", exc_info=True)
        try:
            self.retry(countdown=60)  # Retry after 1 minute
        except MaxRetriesExceededError:
            logger.error("Max retries exceeded for firehose ingestion")
            raise 