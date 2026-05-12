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
    "ufsa.ufl.edu",
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
    "team@mail.perplexity.ai"
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
    "application has been submitted",
    "thank you for applying",
    "we received your application",
    "we've received your application",
    "your application was received",
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
    "submission received",
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
    "your application is under review",
    "we are reviewing your application",
    "we're reviewing your application",
    "reviewing your application",
    "we look forward to reviewing",
    "your application was sent",
    "application was sent to",
    "submitted for the role",
    "your profile has been submitted",
    "we will review your application",
    "your application will be reviewed",
    "keep you updated",
    "we'll be in touch",
    "we will be in touch",
    "be in touch soon",
    "myworkday.com",
    "greenhouse",
    "icims",
    "taleo",
    "smartrecruiters",
    "jobvite",
    "ashbyhq",
    "hire.lever.co",
    "workday",
    "breezy.hr",
    "bamboohr",
    "rippling",
    "jazz.co",
    "jazzhr",
    "recruitee",
    "pinpointhq",
    "dover.com",
    "gem.com",
]

rejected_keywords = [
    "unfortunately we will not",
    "unfortunately your application",
    "unfortunately we are unable",
    "unfortunately, we",
    "unfortunately we",
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
    "we are moving forward with other",
    "moving forward with other applicants",
    "moving forward with other candidates",
    "not the right fit",
    "not a fit",
    "not a match",
    "we will not be proceeding",
    "your application was not selected",
    "we've decided to go with",
    "we've decided to move",
    "decided to go in a different direction",
    "decided to move in a different direction",
    "no longer considering",
    "no longer under consideration",
    "we chose to move forward with another",
    "chosen another candidate",
    "selected another candidate",
    "we went with another",
    "we have gone with another",
    "did not move forward",
    "we regret",
    "wish you the best in your search",
    "wish you all the best",
    "best of luck in your",
    "future endeavors",
    "encourage you to apply again",
    "keep you in mind for future",
    "we'll keep your resume on file",
    "we are unable to move forward",
    "we're unable to move forward",
    "we're going to pass",
    "not be proceeding",
    "have decided not to move forward",
    "after reviewing your background",
    "after reviewing your resume",
    "after reviewing your qualifications",
    "does not meet our current",
    "your qualifications do not",
    "your experience does not",
    "thank you for your time, however",
    "thank you for your time, but",
    "thank you for interviewing",
    "we have filled this position",
    "the role has been filled",
    "this position has been filled",
    "we have moved forward with",
    "we've moved forward with",
    "at this time we",
    "at this time, we",
    "unfortunately, at this time",
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
    skipped_year = skipped_domain = skipped_email = skipped_subject = skipped_context = 0
    min_year = int(os.getenv("MIN_YEAR", 2024))
    print(f"\n[{label}] Scanning: {os.path.basename(path)} ({total} emails, min year: {min_year})")

    for i, message in enumerate(mbox, 1):
        if i % 50 == 0 or i == total:
            print(f"\r  Progress: {i}/{total} ({(i / total) * 100:.0f}%)", end="", flush=True)

        subject = (message["subject"] or "").lower()
        sender = (message["from"] or "").lower()
        date = message["date"] or ""

        try:
            email_date = parsedate_to_datetime(date)
            if email_date.year < min_year:
                skipped_year += 1
                continue
        except (ValueError, TypeError):
            skipped_year += 1
            continue

        is_whitelisted = any(w in sender for w in whitelisted_senders)

        if not is_whitelisted:
            if any(sender.endswith(domain) or f"@{domain}" in sender for domain in blocked_domains):
                skipped_domain += 1
                continue
        if any(blocked in sender for blocked in blocked_emails):
            skipped_email += 1
            continue
        if any(blocked in subject for blocked in blocked_subjects):
            skipped_subject += 1
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

        if not any(kw in text for kw in job_context_keywords):
            skipped_context += 1
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

    passed_filters = total - skipped_year - skipped_domain - skipped_email - skipped_subject
    print(f"\n")
    print(f"  [{label}] Filter breakdown:")
    print(f"    Total emails:       {total}")
    print(f"    Skipped (year):     {skipped_year}")
    print(f"    Skipped (domain):   {skipped_domain}")
    print(f"    Skipped (email):    {skipped_email}")
    print(f"    Skipped (subject):  {skipped_subject}")
    print(f"    Passed filters:     {passed_filters}")
    print(f"    No job context:     {skipped_context}")
    print(f"    Categorized:        {applied_count + rejected_count + action_count}")
    print(f"  -- Applied: {applied_count}  Rejected: {rejected_count}  Action: {action_count}")

# ── Deduplicate ──────────────────────────────────────────
# same company + same category = count once
# keep the most recent email for each combo

seen = {}
for r in results:
    # deduplicate on company + first 60 chars of subject to allow multiple roles at same company
    subject_key = r["subject"].lower()[:60].strip()
    key = (r["company"], r["category"], subject_key)
    if key not in seen:
        seen[key] = r
    else:
        seen[key] = r

deduped = list(seen.values())

deduped_applied = sum(1 for r in deduped if r["category"] == "Applied")
deduped_rejected = sum(1 for r in deduped if r["category"] == "Rejected")
deduped_action = sum(1 for r in deduped if r["category"] == "Action/Next Step")

# ── Results ──────────────────────────────────────────────

total_applied = sum(1 for r in results if r["category"] == "Applied")
total_rejected = sum(1 for r in results if r["category"] == "Rejected")
total_action = sum(1 for r in results if r["category"] == "Action/Next Step")

print(f"\n{'='*50}")
print(f"  REJECTIONS")
print(f"    Total (raw):      {total_rejected}")
print(f"    Unique companies: {deduped_rejected}")
if deduped_applied > 0:
    rate = deduped_rejected / deduped_applied * 100
    print(f"    Rejection rate:   {rate:.0f}% of applied")
print(f"{'='*50}")
print(f"  FULL SUMMARY (deduplicated by company)")
print(f"    Applied:          {deduped_applied}")
print(f"    Rejected:         {deduped_rejected}")
print(f"    Action/Next Steps:{deduped_action}")
print(f"{'-'*50}")
print(f"  RAW (all matched emails)")
print(f"    Applied:          {total_applied}")
print(f"    Rejected:         {total_rejected}")
print(f"    Action/Next Steps:{total_action}")
print(f"{'='*50}")

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