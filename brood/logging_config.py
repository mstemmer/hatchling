# Logging configuration module - sets up custom PHASE logging level
import logging
import time

# Define custom PHASE logging level (between INFO and DEBUG)
PHASE_LEVEL = 25  # Between INFO (20) and DEBUG (10)
logging.addLevelName(PHASE_LEVEL, 'PHASE')

def phase(self, message, *args, **kws):
    """Log a message with severity 'PHASE'."""
    if self.isEnabledFor(PHASE_LEVEL):
        self._log(PHASE_LEVEL, message, args, **kws)

# Add the phase method to the Logger class
logging.Logger.phase = phase


class NumExprFilter(logging.Filter):
    """Filter to suppress NumExpr-related log messages"""
    def filter(self, record):
        # Suppress NumExpr and threading-related messages
        if 'NumExpr' in record.getMessage():
            return False
        if 'numexpr' in record.getMessage().lower():
            return False
        if 'threading' in record.getMessage().lower() and 'thread' in record.getMessage().lower():
            return False
        return True


def setup_logging_for_spawn(log_file_path):
    """
    Configure logging for spawned child processes.
    Called by each child process to set up file handlers.
    
    Args:
        log_file_path: Full path to the log file to write to
    """
    import os
    
    # Retry logic to handle race conditions with file creation
    max_retries = 10
    base_delay = 0.05  # Start with shorter delay
    
    for attempt in range(max_retries):
        try:
            # Ensure log directory exists
            log_dir = os.path.dirname(log_file_path)
            if not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            
            # Wait for log file to be accessible
            # The parent process creates the file, we just need to wait for it
            if not os.path.exists(log_file_path):
                # File doesn't exist yet, wait and retry
                if attempt < max_retries - 1:
                    time.sleep(base_delay * (2 ** attempt))  # Exponential backoff
                    continue
                else:
                    # Last attempt - create it ourselves as fallback
                    with open(log_file_path, 'a') as f:
                        pass
            
            # Clear any existing handlers
            logger = logging.getLogger()
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
            
            # Set up file and console handlers
            log_format = logging.Formatter('%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
            numexpr_filter = NumExprFilter()
            
            # Open file in append mode
            file_handler = logging.FileHandler(log_file_path, mode='a')
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(log_format)
            file_handler.addFilter(numexpr_filter)
            
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(log_format)
            console_handler.addFilter(numexpr_filter)
            
            logging.basicConfig(
                format='%(asctime)s %(levelname)s: %(message)s',
                level=logging.INFO,
                handlers=[file_handler, console_handler],
                datefmt='%Y-%m-%d %H:%M:%S',
                force=True  # Override any existing basicConfig
            )
            
            # Success - exit retry loop
            return
            
        except (FileNotFoundError, OSError, IOError) as e:
            if attempt < max_retries - 1:
                # Wait longer each time
                time.sleep(base_delay * (2 ** attempt))
            else:
                # Final attempt failed - log to console only and continue
                logger = logging.getLogger()
                for handler in logger.handlers[:]:
                    logger.removeHandler(handler)
                
                console_handler = logging.StreamHandler()
                console_handler.setLevel(logging.INFO)
                log_format = logging.Formatter('%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
                console_handler.setFormatter(log_format)
                console_handler.addFilter(NumExprFilter())
                
                logging.basicConfig(
                    format='%(asctime)s %(levelname)s: %(message)s',
                    level=logging.INFO,
                    handlers=[console_handler],
                    datefmt='%Y-%m-%d %H:%M:%S',
                    force=True
                )
                # Don't exit - just log warning and continue with console-only logging
                logging.warning(f"Failed to set up file logging after {max_retries} attempts. Using console logging only.")
                logging.warning(f"Log file path: {log_file_path}")
                logging.warning(f"Error: {str(e)}")
                return
