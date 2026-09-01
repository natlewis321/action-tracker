"""Seed 50 test actions with realistic governance data."""
import random
from datetime import date, timedelta
from models.db import get_db, query_db
from models.action import create_action

ACTIONS = [
    ("Review interest rate risk appetite statement", "Annual review of IRRBB appetite metrics and limits as per ALCO terms of reference", 1, 2),
    ("Update liquidity contingency funding plan", "Refresh CFP stress scenarios and trigger points following PRA feedback", 3, 2),
    ("Complete ICAAP stress testing refresh", "Run updated stress scenarios for capital adequacy assessment", 3, 1),
    ("Board risk appetite dashboard enhancement", "Add mortgage arrears trend and concentration metrics to quarterly Board MI", 1, 3),
    ("Remediate internal audit finding on IT change management", "Audit finding ref IA-2026-03: insufficient testing evidence for system changes", 2, 4),
    ("PRA SREP action — improve operational resilience documentation", "Document important business services and set impact tolerances per SS1/21", 3, 4),
    ("Review outsourcing register", "Annual review of critical and important outsourcing arrangements", 1, 2),
    ("Mortgage conduct risk assessment update", "Refresh conduct risk assessment for residential mortgage book", 1, 3),
    ("Implement new sanctions screening process", "Upgrade AML/sanctions screening in line with updated JMLSG guidance", 3, 2),
    ("Complete annual MLRO report", "Prepare and present annual MLRO report to Board", 1, 2),
    ("Review savings product governance framework", "Assess FCA Consumer Duty compliance for savings products", 3, 1),
    ("Update business continuity plan", "Annual BCP review and test including cyber incident scenario", 2, 4),
    ("Capital planning model validation", "Independent validation of ICAAP capital planning model assumptions", 2, 1),
    ("Review mortgage underwriting policy", "Annual review of lending criteria and affordability methodology", 1, 3),
    ("Internal audit follow-up — data governance", "Closure evidence required for IA-2025-11 data quality findings", 2, 2),
    ("FCA Consumer Duty annual review", "Board attestation and annual review of Consumer Duty implementation", 3, 3),
    ("Update fraud risk assessment", "Annual fraud risk assessment refresh incorporating emerging threats", 2, 2),
    ("Review complaints handling MI", "Enhance root cause analysis reporting for FOS complaints", 1, 2),
    ("Operational risk event reporting enhancement", "Improve near-miss capture and escalation thresholds", 2, 1),
    ("Climate risk scenario analysis", "Develop climate risk scenarios for mortgage portfolio stress testing", 3, 1),
    ("Treasury counterparty limit review", "Annual review of counterparty credit limits and approved list", 1, 2),
    ("Remediate audit finding on succession planning", "Audit finding IA-2026-05: gaps in senior management succession plans", 2, 3),
    ("DORA compliance gap analysis", "Assess readiness for Digital Operational Resilience Act requirements", 3, 4),
    ("Review TCF outcomes monitoring framework", "Update Treating Customers Fairly monitoring metrics and thresholds", 1, 2),
    ("Update credit risk policy", "Refresh credit risk policy to reflect updated HPI methodology", 1, 1),
    ("PRA regulatory returns process review", "Ensure accuracy and timeliness of PRA statistical returns", 3, 1),
    ("Board effectiveness review action plan", "Implement recommendations from external Board effectiveness review", 1, 3),
    ("Whistleblowing policy annual review", "Annual review and Board approval of whistleblowing arrangements", 1, 4),
    ("Review IT disaster recovery plan", "Test and update DR plan including cloud migration changes", 2, 4),
    ("Mortgage arrears management procedure update", "Refresh collections and recoveries procedures for FCA compliance", 1, 3),
    ("Complete vulnerable customer training programme", "Mandatory staff training on vulnerable customer identification and support", 4, 2),
    ("Review liquidity stress testing assumptions", "Validate retail deposit behavioural assumptions in liquidity stress model", 1, 2),
    ("Remediate audit finding on model risk", "IA-2026-07: improve model inventory and validation scheduling", 2, 1),
    ("Update data protection impact assessments", "Review DPIAs for all high-risk processing activities", 4, 4),
    ("Climate-related financial disclosures preparation", "Prepare TCFD-aligned disclosures for annual report", 3, 1),
    ("Review third-party risk management framework", "Enhance due diligence and ongoing monitoring of critical suppliers", 1, 2),
    ("Implement enhanced transaction monitoring rules", "Deploy updated AML transaction monitoring scenarios", 3, 2),
    ("Review remuneration policy for material risk takers", "Annual review per PRA Remuneration Code requirements", 1, 3),
    ("Internal audit plan 2027 approval", "Present risk-based audit plan for Board Audit Committee approval", 2, 4),
    ("Review EBA guidelines on loan origination", "Gap analysis against EBA GL/2020/06 requirements", 3, 3),
    ("Update information security policy", "Annual review of InfoSec policy including ransomware response", 2, 4),
    ("Mortgage product fair value assessment", "Consumer Duty fair value assessment for all mortgage products", 3, 1),
    ("Review AML/CTF risk assessment", "Annual business-wide money laundering risk assessment", 1, 2),
    ("PRA supervisory statement implementation tracker", "Track implementation status of all applicable PRA SSs", 3, 2),
    ("Update risk register", "Quarterly risk register refresh with emerging risk horizon scan", 1, 1),
    ("Review operational resilience self-assessment", "Annual self-assessment of compliance with SS1/21", 3, 2),
    ("Remediate audit finding on vendor management", "IA-2026-09: SLA monitoring gaps for outsourced services", 2, 4),
    ("Prepare for FCA mortgage market review", "Prepare evidence pack and data for FCA thematic review", 3, 3),
    ("Complete annual compliance monitoring plan", "Execute risk-based compliance monitoring programme", 2, 2),
    ("Review pension fund investment strategy", "Review defined benefit scheme investment strategy and funding", 4, 1),
]

PRIORITIES = ['Critical', 'High', 'Medium', 'Low']
PRIORITY_WEIGHTS = [0.08, 0.25, 0.45, 0.22]

# Committee IDs: 1=Board Risk, 2=ALCO, 3=Board, 4=Audit Committee
# Department IDs: 1=Finance, 2=Risk & Compliance, 3=Underwriting, 4=IT
# Category IDs: 1=Committee, 2=Internal Audit, 3=Regulator, 4=Other
# Status IDs: 1=Recorded, 2=In Progress, 3=Completed, 4=Closed
# User IDs: 1=Admin, 2=Nat Lewis

def seed_actions():
    db = get_db()
    random.seed(42)
    today = date.today()

    # Ensure committees and departments exist
    default_committees = ['Board Risk Committee', 'ALCO', 'Board', 'Audit Committee']
    for name in default_committees:
        db.execute("INSERT OR IGNORE INTO config_committees (name) VALUES (?)", (name,))
    default_departments = ['Finance', 'Risk & Compliance', 'Underwriting', 'IT']
    for name in default_departments:
        db.execute("INSERT OR IGNORE INTO config_departments (name) VALUES (?)", (name,))
    db.commit()

    existing_users = query_db(db, "SELECT id FROM users WHERE is_active = 1")
    user_ids = [r['id'] for r in existing_users] if existing_users else [1]
    existing_committees = query_db(db, "SELECT id FROM config_committees WHERE is_active = 1")
    committee_ids = [r['id'] for r in existing_committees]
    existing_depts = query_db(db, "SELECT id FROM config_departments WHERE is_active = 1")
    dept_ids = [r['id'] for r in existing_depts]

    for i, (title, desc, category_id, dept_id) in enumerate(ACTIONS):
        # Date raised: spread over last 6 months
        days_ago = random.randint(10, 180)
        date_raised = today - timedelta(days=days_ago)

        # Due dates: mix of past (overdue), near-future, and further out
        bucket = random.random()
        if bucket < 0.25:
            # Overdue: due date in the past
            due_offset = random.randint(-60, -1)
        elif bucket < 0.45:
            # Due soon (within 14 days)
            due_offset = random.randint(0, 14)
        else:
            # Future
            due_offset = random.randint(15, 120)
        due_date = today + timedelta(days=due_offset)

        # Priority weighted towards Medium
        priority = random.choices(PRIORITIES, weights=PRIORITY_WEIGHTS, k=1)[0]

        # Status: overdue ones mostly still open; future ones can be any status
        if due_offset < 0:
            status_id = random.choice([1, 2])  # Recorded or In Progress
        elif bucket < 0.45:
            status_id = random.choice([1, 2, 2])  # Mostly In Progress
        else:
            status_id = random.choices([1, 2, 3, 4], weights=[0.2, 0.35, 0.3, 0.15], k=1)[0]

        source_committee_id = random.choice(committee_ids)
        reporting_committee_id = random.choice(committee_ids)

        owner_id = random.choice(user_ids)
        exec_sponsor_id = random.choice(user_ids)

        data = {
            'title': title,
            'description': desc,
            'category_id': category_id,
            'source_committee_id': source_committee_id,
            'reporting_committee_id': reporting_committee_id,
            'department_id': dept_ids[(dept_id - 1) % len(dept_ids)] if dept_ids else None,
            'date_raised': date_raised.isoformat(),
            'due_date': due_date.isoformat(),
            'priority': priority,
            'status_id': status_id,
            'owner_id': owner_id,
            'exec_sponsor_id': exec_sponsor_id,
        }

        create_action(db, random.choice(user_ids), data)

    db.close()
    print(f"Seeded {len(ACTIONS)} actions.")


if __name__ == '__main__':
    seed_actions()
