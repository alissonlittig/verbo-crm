"""Deterministic fictional seed data for the Verbo demo. No real people, no real contacts."""
from __future__ import annotations

import random
from datetime import date, timedelta

import pandas as pd

STAGES = ["New", "Contacted", "Trial class", "Proposal", "Won", "Lost"]
OPEN_STAGES = STAGES[:4]
LANGS = ["English", "Spanish", "French", "German", "Italian", "Japanese"]
LEVELS = ["A1", "A2", "B1", "B2", "C1"]
PLANS = {"Essential": 289.0, "Plus": 389.0, "Intensive": 549.0, "Corporate": 790.0}
SOURCES = ["Instagram", "Google", "Referral", "Walk-in", "Corporate", "Open day"]
TEACHERS = ["Marina Alves", "Tom Reyes", "Camille Roche", "Lukas Brandt", "Yuki Tanaka", "Giulia Ferri"]
FIRST = ["Ana", "Bruno", "Carla", "Diego", "Elisa", "Felipe", "Gabi", "Hugo", "Iris", "João", "Karen", "Leo",
         "Marta", "Nico", "Olivia", "Paulo", "Rita", "Sami", "Tânia", "Vitor", "Bia", "Caio", "Dani", "Enzo"]
LAST = ["Prado", "Moura", "Nunes", "Castro", "Lima", "Rocha", "Duarte", "Teixeira", "Barros", "Pires",
        "Matos", "Siqueira", "Farias", "Cardoso", "Ramos", "Viana"]
FIXED = {"Rent": 6800.0, "Software": 890.0, "Utilities": 1250.0, "Admin": 3400.0}
LANG_W = [40, 20, 12, 10, 8, 10]


def month_start(d: date, back: int = 0) -> date:
    k = d.year * 12 + d.month - 1 - back
    return date(k // 12, k % 12 + 1, 1)


def build_seed(today: date | None = None, seed: int = 7) -> dict[str, pd.DataFrame]:
    today = today or date.today()
    r = random.Random(seed)

    def name() -> str:
        return f"{r.choice(FIRST)} {r.choice(LAST)}"

    leads = []
    for i in range(1, 61):
        plan = r.choice(list(PLANS))
        leads.append({
            "id": i, "name": name(), "language": r.choices(LANGS, LANG_W)[0],
            "source": r.choice(SOURCES), "stage": r.choices(STAGES, [14, 12, 10, 8, 14, 6])[0],
            "plan": plan, "value": PLANS[plan], "owner": r.choice(["Paula", "Rafael", "Sofia"]),
            "created": today - timedelta(days=r.randint(0, 75)),
        })

    students, contracts = [], []
    for i in range(1, 91):
        plan = r.choices(list(PLANS), [38, 30, 18, 14])[0]
        start = today - timedelta(days=r.randint(20, 540))
        end = start + timedelta(days=30 * r.choice([6, 12, 12, 12, 18]))
        status = "Active" if end >= today else "Expired"
        if status == "Active" and (end - today).days <= 45:
            status = "Ending soon"
        students.append({"id": i, "name": name(), "language": r.choices(LANGS, LANG_W)[0],
                         "level": r.choice(LEVELS), "plan": plan, "since": start,
                         "status": "Inactive" if status == "Expired" else "Active", "teacher": r.choice(TEACHERS)})
        contracts.append({"id": 1000 + i, "student_id": i, "plan": plan, "monthly": PLANS[plan],
                          "start": start, "end": end, "status": status})

    classes, cid = [], 1
    monday = today - timedelta(days=today.weekday())
    for day in range(6):
        for slot in ["08:00", "10:00", "14:00", "16:00", "19:00", "20:30"]:
            if r.random() < 0.55:
                cap = r.choice([6, 8, 10])
                classes.append({"id": cid, "date": monday + timedelta(days=day), "time": slot,
                                "language": r.choice(LANGS[:4]), "level": r.choice(LEVELS),
                                "teacher": r.choice(TEACHERS), "room": r.choice(["Room 1", "Room 2", "Room 3", "Online"]),
                                "enrolled": r.randint(2, cap), "capacity": cap})
                cid += 1

    tx = []
    now_active = int(sum(c["status"] != "Expired" for c in contracts))
    for back in range(6, -1, -1):
        ms = month_start(today, back)
        n_act = round(now_active * (1 - 0.045 * back) + r.randint(-2, 2))
        tuition = sum(r.choices(list(PLANS.values()), [38, 30, 18, 14])[0] for _ in range(n_act))
        tx += [
            (ms + timedelta(days=4), "Revenue", "Tuition", "Monthly tuition", round(tuition, 2)),
            (ms + timedelta(days=9), "Revenue", "Enrollment fees", "New enrollments", r.randint(3, 8) * 120.0),
            (ms + timedelta(days=12), "Revenue", "Materials", "Books and workbooks", r.randint(15, 30) * 62.0),
            (ms + timedelta(days=27), "Cost", "Teachers", "Teaching payroll", round(n_act * 105.0 + r.randint(-400, 400), 2)),
            (ms + timedelta(days=14), "Expense", "Marketing", "Ads and open day", float(r.randint(2200, 3600))),
        ]
        tx += [(ms + timedelta(days=5), "Expense", c, c, round(v * r.uniform(0.97, 1.04), 2)) for c, v in FIXED.items()]
    tx = pd.DataFrame(tx, columns=["date", "type", "category", "description", "amount"])
    tx = tx[tx["date"] <= today].sort_values("date").reset_index(drop=True)
    tx.insert(0, "id", range(1, len(tx) + 1))
    return {"leads": pd.DataFrame(leads), "students": pd.DataFrame(students), "contracts": pd.DataFrame(contracts),
            "classes": pd.DataFrame(classes), "tx": tx}
