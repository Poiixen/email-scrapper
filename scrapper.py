import win32com.client
import os
from dotenv import load_dotenv

load_dotenv()

outlook = win32com.client.Dispatch("Outlook.Application")
namespace = outlook.GetNamespace("MAPI")
namespace.Logon()

pst_path = os.getenv("PST_PATH")    # school acc
pst_path2 = os.getenv("PST_PATH2")  # personal acc

# capture store count before adding so we index correctly
before = namespace.Stores.Count
namespace.AddStore(pst_path)
namespace.AddStore(pst_path2)

school_store = namespace.Stores[before + 1]
personal_store = namespace.Stores[before + 2]


def count_emails(folder, applied_kw, rejected_kw, action_kw):
    applied = 0
    rejected = 0
    action = 0

    for item in folder.Items:
        # 43 == olMail — skip calendar invites, contacts, etc.
        if item.Class != 43:
            continue

        try:
            subject = (item.Subject or "").lower()
            body = (item.Body or "").lower()
            text = subject + " " + body

            # action first (interviews, next steps) — highest priority
            if any(key in text for key in action_kw):
                action += 1
            # rejections before applied since rejection emails usually
            # also contain "thank you for applying"
            elif any(key in text for key in rejected_kw):
                rejected += 1
            elif any(key in text for key in applied_kw):
                applied += 1

        except AttributeError:
            print(f"Skipping malformed item in {folder.Name}")

    # recurse into subfolders
    for subfolder in folder.Folders:
        a, r, act = count_emails(subfolder, applied_kw, rejected_kw, action_kw)
        applied += a
        rejected += r
        action += act

    return applied, rejected, action


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

try:
    a1, r1, act1 = count_emails(
        school_store.GetRootFolder(), applied_keywords, rejected_keywords, action_keywords
    )
    a2, r2, act2 = count_emails(
        personal_store.GetRootFolder(), applied_keywords, rejected_keywords, action_keywords
    )

    total_applied = a1 + a2
    total_rejected = r1 + r2
    total_action = act1 + act2

    print(f"Total applied: {total_applied}")
    print(f"Total rejected: {total_rejected}")
    print(f"Total action required / next step: {total_action}")

finally:
    namespace.RemoveStore(school_store.GetRootFolder())
    namespace.RemoveStore(personal_store.GetRootFolder())