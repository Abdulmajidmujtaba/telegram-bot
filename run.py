#!/usr/bin/env python
"""
Entry point for the Telegram Summary Bot application.

This script configures logging, sets up signal handlers for graceful shutdown,
and runs the main asynchronous bot logic.
"""
import asyncio
import logging
import signal
import sys
import platform
import os
from bot.main import main
from bot.config import LOG_LEVEL, LOG_FORMAT

# Configure logging
logging.basicConfig(
    format=LOG_FORMAT,
    level=getattr(logging, LOG_LEVEL),
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Setup signal handlers for graceful shutdown
shutdown_event = asyncio.Event()
force_shutdown = False

def signal_handler(sig, frame):
    """
    Handles termination signals (SIGINT, SIGTERM) to initiate graceful shutdown.

    Sets the global `shutdown_event` to signal the main loop to stop.
    Sets `force_shutdown` to True, so a second signal forces an immediate exit.
    """
    global force_shutdown
    
    if force_shutdown:
        logger.info("Forcing immediate shutdown...")
        os._exit(1)  # Force exit without cleanup
        
    logger.info(f"Received signal {sig}, shutting down...")
    shutdown_event.set()
    force_shutdown = True  # Next Ctrl+C will force exit

async def run_with_timeout():
    """Run the main function with a timeout for graceful shutdown."""
    main_task = asyncio.create_task(main())
    
    def handle_main_done(task):
        if task.exception():
            logger.error(f"Main task failed with error: {task.exception()}")
    
    main_task.add_done_callback(handle_main_done)
    
    try:
        await main_task
    except asyncio.CancelledError:
        logger.info("Main task was cancelled")
    except Exception as e:
        logger.error(f"Error in main task: {str(e)}", exc_info=True)
    finally:
        if not main_task.done():
            logger.info("Cancelling main task...")
            main_task.cancel()
            try:
                await asyncio.wait_for(main_task, timeout=5)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                logger.warning("Main task did not complete shutdown in time")

if __name__ == "__main__":
    # Set up signal handlers in a platform-independent way
    if platform.system() != "Windows":
        # Unix-like systems can use asyncio's signal handling
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda s=sig: signal_handler(s, None))
    else:
        # Windows needs to use the signal module directly
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, signal_handler)
    
    try:
        logger.info("Starting Telegram Summary Bot...")
        asyncio.run(run_with_timeout())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user. Exiting...")
    except Exception as e:
        logger.error(f"Error running bot: {str(e)}", exc_info=True)
    finally:
        # Final exit message
        logger.info("Bot has exited")
        sys.exit(0) 