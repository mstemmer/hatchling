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
