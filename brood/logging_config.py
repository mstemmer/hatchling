# Logging configuration module - sets up custom PHASE logging level
import logging

# Define custom PHASE logging level (between INFO and DEBUG)
PHASE_LEVEL = 25  # Between INFO (20) and DEBUG (10)
logging.addLevelName(PHASE_LEVEL, 'PHASE')

def phase(self, message, *args, **kws):
    """Log a message with severity 'PHASE'."""
    if self.isEnabledFor(PHASE_LEVEL):
        self._log(PHASE_LEVEL, message, args, **kws)

# Add the phase method to the Logger class
logging.Logger.phase = phase

def setup_logging_for_spawn(log_file_path):
    """
    Configure logging for spawned child processes.
    Called by each child process to set up file handlers.
    
    Args:
        log_file_path: Full path to the log file to write to
    """
    # Clear any existing handlers
    logger = logging.getLogger()
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Set up file and console handlers
    log_format = logging.Formatter('%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(log_format)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(log_format)
    
    logging.basicConfig(
        format='%(asctime)s %(levelname)s: %(message)s',
        level=logging.INFO,
        handlers=[file_handler, console_handler],
        datefmt='%Y-%m-%d %H:%M:%S',
        force=True  # Override any existing basicConfig
    )
