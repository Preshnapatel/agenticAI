import sqlite3
import random
from faker import Faker
from pathlib import Path

fake = Faker()
Faker.seed(42)
random.seed(42)

DB_PATH = Path(__file__).parent / "customers.db"

CATEGORIES = ["Billing", "Technical", "Shipping", "Returns", "General Inquiry"]
STATUSES = ["Open", "In Progress", "Resolved", "Closed"]
PRIORITIES = ["Low", "Medium", "High", "Critical"]
PLANS = ["Free", "Basic", "Pro", "Enterprise"]

def seed():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.executescript("""
        DROP TABLE IF EXISTS support_tickets;
        DROP TABLE IF EXISTS customers;

        CREATE TABLE customers (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT    NOT NULL,
            email         TEXT    UNIQUE NOT NULL,
            phone         TEXT,
            company       TEXT,
            plan          TEXT,
            country       TEXT,
            created_at    TEXT
        );

        CREATE TABLE support_tickets (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id   INTEGER NOT NULL,
            title         TEXT    NOT NULL,
            description   TEXT,
            category      TEXT,
            status        TEXT,
            priority      TEXT,
            created_at    TEXT,
            resolved_at   TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        );
    """)

    customer_ids = []
    for _ in range(50):
        cur.execute("""
            INSERT INTO customers (name, email, phone, company, plan, country, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            fake.name(),
            fake.unique.email(),
            fake.phone_number(),
            fake.company(),
            random.choice(PLANS),
            fake.country(),
            fake.date_between(start_date="-2y", end_date="today").isoformat(),
        ))
        customer_ids.append(cur.lastrowid)

    cur.execute("""
        INSERT INTO customers (name, email, phone, company, plan, country, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        "Ema Johnson",
        "ema.johnson@example.com",
        "+1-555-0199",
        "Acme Corp",
        "Pro",
        "United States",
        "2024-01-15"
    ))
    ema_id = cur.lastrowid
    customer_ids.append(ema_id)

    sample_tickets = [
        ("Unable to login to dashboard", "Getting 401 error on every login attempt.", "Technical"),
        ("Invoice shows wrong amount", "I was charged $99 but my plan is $49.", "Billing"),
        ("Package not delivered", "Order #8821 shipped 2 weeks ago, no update.", "Shipping"),
        ("Request refund for duplicate charge", "Charged twice on March 1st.", "Returns"),
        ("How do I export my data?", "Looking for CSV export option.", "General Inquiry"),
        ("App crashes on mobile", "iOS app crashes when opening reports tab.", "Technical"),
        ("Upgrade plan", "Want to move from Basic to Pro.", "Billing"),
        ("Wrong item shipped", "Received blue widget, ordered red widget.", "Shipping"),
    ]

    for cid in customer_ids:
        num_tickets = random.randint(1, 5)
        for _ in range(num_tickets):
            title, desc, cat = random.choice(sample_tickets)
            status = random.choice(STATUSES)

            created_date = fake.date_between(start_date="-1y", end_date="today")
            created = created_date.isoformat()

            resolved = (
                fake.date_between(start_date=created_date, end_date="today").isoformat()
                if status in ("Resolved", "Closed")
                else None
            )

            cur.execute("""
                INSERT INTO support_tickets
                    (customer_id, title, description, category, status, priority, created_at, resolved_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cid,
                title,
                desc,
                cat,
                status,
                random.choice(PRIORITIES),
                created,
                resolved
            ))

    conn.commit()
    conn.close()

    print(f"✅ Database seeded at {DB_PATH}")
    print(f"Customers : {len(customer_ids)}")

    conn2 = sqlite3.connect(DB_PATH)
    cur2 = conn2.cursor()
    cur2.execute("SELECT COUNT(*) FROM support_tickets")
    print(f"Tickets   : {cur2.fetchone()[0]}")
    conn2.close()

if __name__ == "__main__":
    seed()