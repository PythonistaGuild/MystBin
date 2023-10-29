import os
from typing import Any
import logging
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

logger = logging.getLogger()

async def send_datapackage(package: str, addr: str, cfg: dict[str, Any]) -> None:
    mail = MIMEMultipart()
    mail["From"] = cfg["mailer"]["from"]
    mail["To"] = addr
    mail["Subject"] = "Your Mystbin data package"
    
    mail.attach(MIMEText("Your data package has arrived!"))

    with open(package, mode="rb") as file:
        part = MIMEApplication(file.read(), name=os.path.basename(package))
        
    part["Content-Disposition"] = f"attachment; filename=DataPackage.zip"
    mail.attach(part)


    try:
        await aiosmtplib.send(
            mail,
            sender=cfg["mailer"]["from"],
            recipients=[addr],
            hostname=cfg["mailer"]["smtp_server"],
            port=cfg["mailer"]["smtp_port"],
            use_tls=True if cfg["mailer"]["smtp_port"] == 465 else False,
            username=cfg["mailer"]["username"],
            password=cfg["mailer"]["password"]
        )
    except:
        logger.exception("Failed to send datapackage email:")
    finally:
        os.remove(package)

GOODBYE_TEXT = """
This email serves as confirmation that your Mystbin account has been deleted.
At this point, we have removed all of your data from our database.
Pastes associated with your account have NOT been deleted, and are no longer tied to any account.

If you need further assistance, please reply to this email.
"""

async def send_goodbye(addr: str, cfg: dict[str, Any]) -> None:
    mail = MIMEMultipart()
    mail["From"] = cfg["mailer"]["from"]
    mail["To"] = addr
    mail["Subject"] = "Goodbye!"
    
    mail.attach(MIMEText(GOODBYE_TEXT))

    try:
        await aiosmtplib.send(
            mail,
            sender=cfg["mailer"]["from"],
            recipients=[addr],
            hostname=cfg["mailer"]["smtp_server"],
            port=cfg["mailer"]["smtp_port"],
            use_tls=True if cfg["mailer"]["smtp_port"] == 465 else False,
            username=cfg["mailer"]["username"],
            password=cfg["mailer"]["password"]
        )
    except:
        logger.exception("Failed to send goodbye email:")
