import mailbox
import os
from dotenv import load_dotenv

load_dotenv()

# after converting your PSTs to .mbox files
mbox_paths = [
    os.getenv("MBOX_PATH"),   # school acc
    os.getenv("MBOX_PATH2"),  # personal acc
]

applied_keywords = [
    "application received",
    "application submitted",
    "thank you for applying",
    "we received your application",
]

rejected_keywords = [
    "unfortunately",
    "not moving forward",
    "other candidates",
    "position has been filled",
    "not selected",
    "regret to inform",
]

action_keywords = [
    "action required",
    "next steps",
    "schedule an interview",
    "interview invitation",
    "move forward",
    "like to invite you",
]

applied, rejected, action = 0, 0, 0

for path in mbox_paths:
    mbox = mailbox.mbox(path)

    for message in mbox:
        subject = (message["subject"] or "").lower()

        # extract body text — handles multipart emails
        body = ""
        if message.is_multipart():
            for part in message.walk():
                if part.get_content_type() == "text/plain":
                    body += part.get_payload(decode=True).decode("utf-8", errors="ignore")
        else:
            body = message.get_payload(decode=True).decode("utf-8", errors="ignore")

        body = body.lower()
        text = subject + " " + body

        if any(kw in text for kw in action_keywords):
            action += 1
        elif any(kw in text for kw in rejected_keywords):
            rejected += 1
        elif any(kw in text for kw in applied_keywords):
            applied += 1

print(f"Applied:  {applied}")
print(f"Rejected: {rejected}")
print(f"Action/Next Steps: {action}")