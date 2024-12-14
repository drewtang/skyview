# Save this as debug.py
import os
import django
import logging
import asyncio
import signal

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skyview.settings')
django.setup()

# Set up logging to see everything
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Import the client directly instead of using the Celery task
from atproto import AsyncFirehoseSubscribeReposClient, parse_subscribe_repos_message, models, CAR
from django.utils import timezone
from ingestion.models import Event

# Global flag for shutdown
shutdown = False

def signal_handler(signum, frame):
    global shutdown
    logger.info("Received shutdown signal")
    shutdown = True

async def message_callback(message):
    try:
        logger.debug("Received message")
        commit = parse_subscribe_repos_message(message)
        
        if isinstance(commit, models.ComAtprotoSyncSubscribeRepos.Commit) and commit.blocks:
            logger.debug("Processing commit with blocks")
            car = CAR.from_bytes(commit.blocks)
            
            for op in commit.ops:
                if (op.action == 'create' and 
                    hasattr(op, 'record') and 
                    getattr(op.record, '$type', None) == 'app.bsky.feed.post'):
                    
                    logger.info(f"Found post from {commit.repo}")
                    Event.objects.create(
                        repo=commit.repo,
                        operation='create',
                        record=op.record,
                        created_at=timezone.now()
                    )

    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)

async def error_callback(error):
    logger.error(f"Firehose error: {error}", exc_info=True)

async def main():
    client = None
    try:
        logger.info("Starting Firehose client...")
        client = AsyncFirehoseSubscribeReposClient()
        
        # Start the client in the background
        client_task = asyncio.create_task(
            client.start(message_callback, error_callback)
        )
        
        # Wait until shutdown is requested
        while not shutdown:
            await asyncio.sleep(1)
            
        logger.info("Shutting down gracefully...")
        if client:
            await client.stop()
            
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
    finally:
        if client:
            try:
                await client.stop()
            except:
                pass

if __name__ == "__main__":
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        logger.info("Starting debug run...")
        asyncio.run(main())
        logger.info("Debug run completed")
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.exception("Error in debug run: %s", e)