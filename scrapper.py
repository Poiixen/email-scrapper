import mailbox
import os
import csv
import re
from email.utils import parsedate_to_datetime
from dotenv import load_dotenv

load_dotenv()

mbox_sources = [
    {"path": os.getenv("MBOX_PATH"),  "label": "School"},
    {"path": os.getenv("MBOX_PATH2"), "label": "Personal"},
]

# ── Filters ──────────────────────────────────────────────

blocked_domains = [
    "ufl.edu",
    "gradescope.com",
    "instructure.com",
    "canvaslms.com",
    "github.com",
    "piazza.com",
    "csm.symplicity.com",
    "floridagators.com",
    "e.floridagators.com",
    "substack.com",
    "leetcode.com",
    "codepath.org",
    "slack.com",
    "rentcafe.com",
    "glassdoor.com",
    "fiu.edu",
    "mail2.wellsfargorewards.com",
    "mheducation.com",
    "jetbrains.com",
    "nscs.org",
    "assetliving.com",
    "everfi.com",
    "progressive.com",
    "e.progressive.com",
    "notificationemails.microsoft.com",
    "palmbeachstate.edu",
    "pronetwork.ufl.edu",
    "bb3.wayup.com",
    "codecademy.com",
    "interviewing.io",
]

blocked_emails = [
    "messages-noreply@linkedin.com",
    "noreply@teams-microsoft.us",
    "dse@docusignmail.net",
    "gatorevals-donotreply@ufl.edu",
    "no-reply@notifications.ufl.edu",
    "donotreply@everfi.com",
    "jennifer@colorstack.org",
    "reply@e.floridagators.com",
    "sales.us@jetbrains.com",
    "notifications@maxient.com",
    "editors-noreply@linkedin.com",
    "jobalerts-noreply@linkedin.com",
    "invitations@linkedin.com",
    "alert@indeed.com",
    "noreply@swelist.com",
    "donotreply@match.indeed.com",
    "info@joinknack.com",
    "learn@itr.mail.codecademy.com",
]

blocked_subjects = [
    "resume book",
    "linkedin learning",
    "transient student",
]

# only these specific senders bypass blocked domains
whitelisted_senders = [
    "joinhandshake.com",
    "codingitforward.com",
]

# email must contain at least one of these to be considered job-related
job_context_keywords = [
    "application",
    "position",
    "role",
    "job",
    "intern",
    "candidate",
    "hiring",
    "recruit",
    "opportunity",
    "employment",
    "offer",
    "interview",
    "resume",
    "apply",
]

# ── Keywords ─────────────────────────────────────────────

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
    "thank you for your interest",
    "thanks for your interest",
    "we appreciate your interest",
    "your submission has been received",
    "application status",
    "you applied",
    "your recent application",
    "applied for",
    "application for the position",
    "thank you for submitting",
    "thanks for submitting",
    "position of interest",
    "candidate portal",
    "candidate profile",
    "myworkday.com",
    "greenhouse",
    "icims",
    "taleo",
    "smartrecruiters",
    "jobvite",
    "ashbyhq",
    "hire.lever.co",
]

rejected_keywords = [
    "unfortunately we will not",
    "unfortunately your application",
    "unfortunately we are unable",
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
    "next steps in the interview",
    "next steps in our process",
    "next steps for your application",
    "schedule an interview",
    "interview invitation",
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
    "schedule a time",
    "book a time",
    "interview scheduled",
    "interview confirmation",
    "virtual onsite",
    "on-site interview",
    "final round",
    "meet the team",
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
    "welcome aboard",
]

# ── Helper: extract company name from sender ─────────────

def extract_company(sender):
    """Pull a rough company name from the sender for deduplication."""
    # try display name first: "Netflix Careers" <noreply@netflix.com>
    if '"' in sender:
        name = sender.split('"')[1].strip()
        if name:
            return name.lower()
    # fallback to domain: noreply@jobs.netflix.com -> netflix
    if '@' in sender:
        domain = sender.split('@')[-1].split('>')[0].strip()
        parts = domain.replace('.com', '').replace('.org', '').replace('.io', '').replace('.net', '').split('.')
        # skip generic prefixes like mail, jobs, careers, noreply
        skip = {'mail', 'jobs', 'careers', 'noreply', 'no-reply', 'e', 'mail1', 'mail2', 'talent', 'hire', 'career', 'alerts', 'recruit', 'notifications'}
        for part in parts:
            if part not in skip and len(part) > 2:
                return part.lower()
    return sender.lower()

# ── Scan ─────────────────────────────────────────────────

results = []

for source in mbox_sources:
    path = source["path"]
    label = source["label"]

    if not path or not os.path.exists(path):
        print(f"\n[{label}] Skipping — path not found")
        continue

    mbox = mailbox.mbox(path)
    total = len(mbox)
    applied_count, rejected_count, action_count = 0, 0, 0
    print(f"\n[{label}] Scanning: {os.path.basename(path)} ({total} emails)")

    for i, message in enumerate(mbox, 1):
        if i % 50 == 0 or i == total:
            print(f"\r  Progress: {i}/{total} ({(i / total) * 100:.0f}%)", end="", flush=True)

        subject = (message["subject"] or "").lower()
        sender = (message["from"] or "").lower()
        date = message["date"] or ""

        
        # whitelist check — only specific senders bypass domain block
        is_whitelisted = any(w in sender for w in whitelisted_senders)

        if not is_whitelisted:
            if any(sender.endswith(domain) or f"@{domain}" in sender for domain in blocked_domains):
                continue
        if any(blocked in sender for blocked in blocked_emails):
            continue
        if any(blocked in subject for blocked in blocked_subjects):
            continue

        # extract body — plain text first, HTML fallback
        body = ""
        html_body = ""
        if message.is_multipart():
            for part in message.walk():
                if part.get_content_type() == "text/plain":
                    payload = part.get_payload(decode=True)
                    if isinstance(payload, bytes):
                        body += payload.decode("utf-8", errors="ignore")
                elif part.get_content_type() == "text/html":
                    payload = part.get_payload(decode=True)
                    if isinstance(payload, bytes):
                        html_body += payload.decode("utf-8", errors="ignore")
        else:
            payload = message.get_payload(decode=True)
            if isinstance(payload, bytes):
                content = payload.decode("utf-8", errors="ignore")
                if message.get_content_type() == "text/html":
                    html_body = content
                else:
                    body = content

        if not body and html_body:
            body = re.sub(r'<[^>]+>', ' ', html_body)

        body = body.lower()
        text = subject + " " + body

        # must look like a job-related email first
        if not any(kw in text for kw in job_context_keywords):
            continue

        # categorize — rejection first to avoid overlap
        category = None
        matched_keyword = None

        if any(kw in text for kw in rejected_keywords):
            category = "Rejected"
            matched_keyword = next(kw for kw in rejected_keywords if kw in text)
            rejected_count += 1
        elif any(kw in text for kw in action_keywords):
            category = "Action/Next Step"
            matched_keyword = next(kw for kw in action_keywords if kw in text)
            action_count += 1
        elif any(kw in text for kw in applied_keywords):
            category = "Applied"
            matched_keyword = next(kw for kw in applied_keywords if kw in text)
            applied_count += 1

        if category:
            results.append({
                "source": label,
                "date": date,
                "from": sender,
                "company": extract_company(sender),
                "subject": (message["subject"] or ""),
                "category": category,
                "matched_keyword": matched_keyword,
                "body_preview": body[:200].replace("\n", " ").strip(),
            })

    print(f"\n\n  [{label}] Applied: {applied_count}")
    print(f"  [{label}] Rejected: {rejected_count}")
    print(f"  [{label}] Action/Next Steps: {action_count}")

# ── Deduplicate ──────────────────────────────────────────
# same company + same category = count once
# keep the most recent email for each combo

seen = {}
for r in results:
    key = (r["company"], r["category"])
    if key not in seen:
        seen[key] = r
    else:
        # keep whichever is more recent (later in the list = more recent from mbox)
        seen[key] = r

deduped = list(seen.values())

deduped_applied = sum(1 for r in deduped if r["category"] == "Applied")
deduped_rejected = sum(1 for r in deduped if r["category"] == "Rejected")
deduped_action = sum(1 for r in deduped if r["category"] == "Action/Next Step")

# ── Results ──────────────────────────────────────────────

total_applied = sum(1 for r in results if r["category"] == "Applied")
total_rejected = sum(1 for r in results if r["category"] == "Rejected")
total_action = sum(1 for r in results if r["category"] == "Action/Next Step")

print(f"\n{'='*40}")
print(f"  RAW (all emails matched)")
print(f"    Applied:          {total_applied}")
print(f"    Rejected:         {total_rejected}")
print(f"    Action/Next Steps:{total_action}")
print(f"{'='*40}")
print(f"  DEDUPLICATED (unique companies)")
print(f"    Applied:          {deduped_applied}")
print(f"    Rejected:         {deduped_rejected}")
print(f"    Action/Next Steps:{deduped_action}")
print(f"{'='*40}")

# write full results
output_file = "results.csv"
with open(output_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["source", "date", "company", "from", "subject", "category", "matched_keyword", "body_preview"])
    writer.writeheader()
    writer.writerows(results)

# write deduplicated results
deduped_file = "results_deduped.csv"
with open(deduped_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["source", "date", "company", "from", "subject", "category", "matched_keyword", "body_preview"])
    writer.writeheader()
    writer.writerows(deduped)

print(f"\nFull results saved to: {output_file}")
print(f"Deduplicated results saved to: {deduped_file}")