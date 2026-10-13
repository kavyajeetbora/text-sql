import csv
import io
import logging
import os

class CSVFormatter(logging.Formatter):
    """Custom formatter to format log records into a valid CSV row."""

    def __init__(self, fieldnames):
        super().__init__()
        self.fieldnames = fieldnames

    def format(self, record):
        # Redirect csv.writer to an in-memory string buffer
        redirect_stdout = io.StringIO()
        writer = csv.DictWriter(
            redirect_stdout, fieldnames=self.fieldnames, lineterminator=""
        )

        # Map logging attributes to your CSV columns
        # You can add custom properties here
        row_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "question": getattr(record, "question", ""),
            "attempt": getattr(record, "attempt", ""),
            "sql": getattr(record, "sql", "").replace("\n", " "),
            "error": getattr(record, "error", ""),
            "message": record.getMessage(),
        }

        writer.writerow(row_data)
        return redirect_stdout.getvalue()


def setup_csv_logger(logger_name, log_file):
    # 1. Define CSV columns
    fieldnames = ["timestamp", "level", "question", "attempt", "sql", "error", "message"]

    # 2. Check if file is empty to write headers
    file_exists = os.path.exists(log_file) and os.path.getsize(log_file) > 0

    if not file_exists:
        with open(log_file, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(fieldnames)

    # 3. Initialize logger and file handler
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)

    # Append mode 'a' keeps historical logs
    file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")

    # 4. Attach custom CSV Formatter
    formatter = CSVFormatter(fieldnames)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


# --- Example Usage ---
if __name__ == "__main__":
    csv_log_path = "app_logs.csv"
    logger = setup_csv_logger("MyCSVLogger", csv_log_path)

    # Standard log entries
    logger.info("Application started successfully.")
    logger.warning("Resource utilization is high.")

    # Even messages containing commas or quotes won't corrupt the CSV layout
    logger.error('Failed to parse data: {"error": "Timeout", "code": 500}')

    print(f"Logs written to {csv_log_path}")
