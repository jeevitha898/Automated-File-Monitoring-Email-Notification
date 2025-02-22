import os
import smtplib
import time
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import psutil

# 🔹 Configure Logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# 🔹 Configuration
FOLDER_TO_WATCH = r"C:\Users\Jeevitha\Desktop\TEST"
SENDER_EMAIL = "jeevithax02@gmail.com"
#eell pxkr nmxq jrnz    jeevithax02@gmail.com"
SENDER_PASSWORD = "jfjy rvuv jqao cwnt"    # Use an App Password
RECIPIENT_EMAILS = ["k74804788@gmail.com", "jeevitha81111@gmail.com"]
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465  

# 🔹 Thread Pool for FAST execution
executor = ThreadPoolExecutor(max_workers=5)

def check_file_ready(file_path, max_retries=10, wait_time=3):
    """Check if the file is ready to be processed."""
    for _ in range(max_retries):
        if os.path.exists(file_path) and os.access(file_path, os.R_OK):
            try:
                with open(file_path, "rb"):
                    logging.debug(f"✅ File is ready: {file_path}")
                    return True
            except PermissionError:
                logging.warning(f"⏳ File is locked, retrying in {wait_time}s...")

        time.sleep(wait_time)
    
    logging.error(f"❌ File is not accessible after {max_retries} retries: {file_path}")
    return False

class FileHandler(FileSystemEventHandler):
    def on_created(self, event):
        """Triggered when a new file is created"""
        if not event.is_directory:
            logging.info(f"📁 New file detected: {event.src_path} (Checking accessibility...)")
            executor.submit(self.process_file, event.src_path)

    def process_file(self, file_path):
        """Waits for the file to be ready and sends email"""
        if check_file_ready(file_path):
            self.send_email(file_path)

    def send_email(self, file_path):
        """Sends email with the newly created file as an attachment"""
        try:
            logging.info(f"📤 Preparing email for {file_path}...")

            # Email message setup
            msg = MIMEMultipart()
            msg["From"] = SENDER_EMAIL
            msg["To"] = ", ".join(RECIPIENT_EMAILS)
            msg["Subject"] = "🆕 New File Notification"

            # Attach the file
            with open(file_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={os.path.basename(file_path)}",
                )
                msg.attach(part)

            # 🔥 Send email instantly using SSL
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.sendmail(SENDER_EMAIL, RECIPIENT_EMAILS, msg.as_string())

            logging.info(f"✅ Email sent successfully for {file_path}")

        except Exception as e:
            logging.error(f"❌ Error sending email: {e}")

# 🔹 Start monitoring the folder
if os.path.exists(FOLDER_TO_WATCH):
    observer = Observer()
    event_handler = FileHandler()
    observer.schedule(event_handler, FOLDER_TO_WATCH, recursive=False)

    logging.info(f"🔍 Monitoring folder: {FOLDER_TO_WATCH}...")

    observer.start()

    try:
        while True:
            time.sleep(2)  # Keeps the script running
            logging.debug("⏳ Monitoring for new files...")
    except KeyboardInterrupt:
        observer.stop()
        logging.info("🛑 Monitoring stopped by user.")

    observer.join()
    executor.shutdown()
else:
    logging.error(f"❌ Folder does not exist: {FOLDER_TO_WATCH}")


