import mailbox
import os
import csv
from dotenv import load_dotenv

load_dotenv()

mbox_paths = [
    os.getenv("MBOX_PATH"),
    os.getenv("MBOX_PATH2"),
]

blocked_senders = [
    "gatorevals-donotreply@ufl.edu",
    "no-reply@gradescope.com",
    "notifications@instructure.com",   # Canvas
    "no-reply@canvaslms.com",
    "@ufl.edu",                         # catch-all for UF system emails — remove if too aggressive
]

applied_keywords = [
    "application received",
    "application submitted",
    "thank you for applying",
    "we received your application",
    "thanks for applying",
    "application has been received",
    "successfully submitted",
    "application confirmation",
    "confirm your application",
    "we have received your application",
    "your application for",
    "applied to",
    "application to",
    "thank you for your interest",
    "thanks for your interest",
    "we appreciate your interest",
    "your submission has been received",
    "application status",
    "you applied",
    "your recent application",
    "applying to",
    "applied for",
    "application for the position",
    "thank you for submitting",
    "thanks for submitting",
    "position of interest",
    "candidate portal",
    "candidate profile",
    "workday",
    "greenhouse",
    "lever",
    "icims",
    "taleo",
    "smartrecruiters",
    "jobvite",
    "ashbyhq",
]

rejected_keywords = [
    "unfortunately",
    "not moving forward",
    "other candidates",
    "position has been filled",
    "not selected",
    "regret to inform",
    "will not be moving forward",
    "unable to offer",
    "decided not to proceed",
    "won't be moving forward",
    "not be advancing",
    "pursued other candidates",
    "after careful consideration",
    "competitive applicant pool",
    "we have decided to move forward with",
    "not the right fit",
    "we will not be proceeding",
    "your application was not selected",
    "we've decided to go with",
    "decided to go in a different direction",
    "no longer considering",
    "we chose to move forward with another",
    "did not move forward",
    "candidacy for",
    "we regret",
    "wish you the best in your search",
    "wish you all the best",
    "best of luck in your",
    "future endeavors",
    "encourage you to apply again",
    "keep you in mind for future",
    "we'll keep your resume on file",
]

action_keywords = [
    "action required",
    "next steps",
    "schedule an interview",
    "interview invitation",
    "move forward",
    "like to invite you",
    "phone screen",
    "technical interview",
    "coding challenge",
    "online assessment",
    "oa invitation",
    "hackerrank",
    "codesignal",
    "hirevue",
    "karat",
    "take-home",
    "complete the assessment",
    "please complete",
    "schedule a time",
    "book a time",
    "calendly",
    "interview scheduled",
    "interview confirmation",
    "virtual onsite",
    "on-site interview",
    "final round",
    "meet the team",
    "hiring manager",
    "recruiter call",
    "recruiter screen",
    "we'd like to move forward",
    "we would like to move forward",
    "pleased to invite",
    "excited to invite",
    "advance your application",
    "progressed to the next",
    "moved to the next stage",
    "offer letter",
    "we are pleased to offer",
    "congratulations",
    "welcome aboard",
    "background check",
]

applied_count, rejected_count, action_count = 0, 0, 0
results = []

for path in mbox_paths:
    if not path or not os.path.exists(path):
        continue

    mbox = mailbox.mbox(path)
    total = len(mbox)
    print(f"\nScanning: {os.path.basename(path)} ({total} emails)")

    for i, message in enumerate(mbox, 1):
        if i % 50 == 0 or i == total:
            pct = (i / total) * 100
            print(f"\r  Progress: {i}/{total} ({pct:.0f}%)", end="", flush=True)

        subject = (message["subject"] or "").lower()
        sender = (message["from"] or "").lower()
        date = message["date"] or ""

        blocked_senders = [
            "gatorevals-donotreply@ufl.edu",
            "no-reply@gradescope.com",
            "notifications@instructure.com",
            "no-reply@canvaslms.com",
            "noreply@github.com",
            "no-reply@piazza.com",
        ]
        if any(blocked in sender for blocked in blocked_senders):
            continue

        body = ""
        if message.is_multipart():
            for part in message.walk():
                if part.get_content_type() == "text/plain":
                    payload = part.get_payload(decode=True)
                    if isinstance(payload, bytes):
                        body += payload.decode("utf-8", errors="ignore")
        else:
            payload = message.get_payload(decode=True)
            if isinstance(payload, bytes):
                body = payload.decode("utf-8", errors="ignore")

        body = body.lower()
        text = subject + " " + body

        category = None
        matched_keyword = None

        if any(kw in text for kw in action_keywords):
            category = "Action/Next Step"
            matched_keyword = next(kw for kw in action_keywords if kw in text)
            action_count += 1
        elif any(kw in text for kw in rejected_keywords):
            category = "Rejected"
            matched_keyword = next(kw for kw in rejected_keywords if kw in text)
            rejected_count += 1
        elif any(kw in text for kw in applied_keywords):
            category = "Applied"
            matched_keyword = next(kw for kw in applied_keywords if kw in text)
            applied_count += 1

        if category:
            results.append({
                "date": date,
                "from": sender,
                "subject": (message["subject"] or ""),
                "category": category,
                "matched_keyword": matched_keyword,
                "body_preview": body[:200].replace("\n", " ").strip(),
            })

    print()

# write CSV
output_file = "results.csv"
with open(output_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["date", "from", "subject", "category", "matched_keyword", "body_preview"])
    writer.writeheader()
    writer.writerows(results)

print(f"\nApplied:  {applied_count}")
print(f"Rejected: {rejected_count}")
print(f"Action/Next Steps: {action_count}")
print(f"\nDetailed results saved to: {output_file}")