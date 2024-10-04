# The logger module is used to configure and create loggers for the application.
# It is used to log messages to the console or a file, with different levels of severity (e.g., info, warning, error).
# In config files, you can specify the log level, format, and handlers (e.g., console, file).
# You can create multiple loggers with different configurations and use them in different parts of the application.
# Please see documentation for more details: https://docs.python.org/3/library/logging.html

# Rational for the Log Levels:
# debug: More verbose output that is useful for development/troubleshooting but not as much to be enabled on production/staging by default
# info: Logs that contain useful information that should be tracked on staging/production
# error: Useful information about relevant errors
# exception: Useful information about relevant errors with the backtrace
# critical: An error that heavily impacts on Top Assist Behaviour (e.g. failed to connect it to Slack) or that causes Top Assist to exit earlier

# Hints:
# 1) You can add any extra details formatted to the message (recommended for better filtering experience):
#    logging.info("Processing page...", { "page_id": page_id, "space_key": space_key })
# 2) Otherwise, you can include some variables to the message directly (not recommended):
#    logging.info("Processing page with ID %s...", page_id, extra={'space_key': space_key})
# 3) You can log exceptions (useful when exception is re-raised):
#    try:
#        # Some code that might raise an exception
#    except Exception:
#        logging.exception("An error occurred")
#        raise
# 4) You can log tracebacks with stack information (useful when exception is captured at the top level):
#    try:
#        # Some code that might raise an exception
#    except Exception:
#        logging.exception("An error occurred", stack_info=True)
