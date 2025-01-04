import logging

formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s - "
    "File: %(filename)s - Line: %(lineno)d - Function: %(funcName)s",
)

payment_file_handler = logging.FileHandler("logs/payment_logs.log")
payment_logger = logging.getLogger("payment_logger")

email_file_handler = logging.FileHandler("logs/email_logs.log")
email_logger = logging.getLogger("email_logger")

# File handler for logging to a file
payment_file_handler.setFormatter(formatter)
email_file_handler.setFormatter(formatter)

# Add the handler to the logger
payment_logger.addHandler(payment_file_handler)
email_logger.addHandler(email_file_handler)
