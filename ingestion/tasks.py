from celery import shared_task
import asyncio
import logging
from atproto import AsyncFirehoseSubscribeReposClient, parse_subscribe_repos_message, models, CAR
from django.utils import timezone
from datetime import timedelta
from .models import Event

logger = logging.getLogger(__name__)

@shared_task(
    bind=True,
    name='ingestion.tasks.start_firehose_ingestion',
    max_retries=None,
    time_limit=None,
    soft_time_limit=None,
    acks_late=True,
)
def start_firehose_ingestion(self):
    """Start the Bluesky firehose ingestion process."""
    try:
        async def message_callback(message):
            try:
                commit = parse_subscribe_repos_message(message)
                
                # Process only commit messages with blocks
                if isinstance(commit, models.ComAtprotoSyncSubscribeRepos.Commit) and commit.blocks:
                    car = CAR.from_bytes(commit.blocks)
                    
                    # Only process 'create' operations that are posts
                    for op in commit.ops:
                        if (op.action == 'create' and 
                            hasattr(op, 'record') and 
                            getattr(op.record, '$type', None) == 'app.bsky.feed.post'):
                            
                            # Store the event
                            Event.objects.create(
                                repo=commit.repo,
                                operation='create',
                                record=op.record,
                                created_at=timezone.now()
                            )
                            logger.info(f"Stored new post from {commit.repo}")

            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)

        async def error_callback(error):
            logger.error(f"Firehose error: {error}", exc_info=True)
                
        async def run_client():
            client = None
            try:
                logger.info("Starting Firehose client...")
                client = AsyncFirehoseSubscribeReposClient()
                await client.start(message_callback, error_callback)
            except Exception as e:
                logger.error(f"Client connection error: {e}", exc_info=True)
                if client:
                    try:
                        await client.stop()
                    except Exception as e:
                        logger.error(f"Error stopping client: {e}", exc_info=True)
                raise
        
        # Run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(run_client())
        finally:
            loop.close()
            
    except Exception as exc:
        logger.error(f"Task failed: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=60)

    return True

@shared_task
def cleanup_old_events():
    """Delete events older than 24 hours"""
    cutoff = timezone.now() - timedelta(hours=24)
    deleted_count = Event.objects.filter(created_at__lt=cutoff).delete()[0]
    if deleted_count > 0:
        logger.info(f"Cleaned up {deleted_count} old events")