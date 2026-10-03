"""Concurrent load test against a running server (NFR-01; NFR-08 from SRS v1.1).

Usage:  python tests/perf/load_test.py --url http://localhost:8000 --users 50 --rounds 10
Requires the demo data from `python -m backend.app.seed`.
Each virtual user logs in, then repeatedly lists complaints, opens one, submits one and reads notifications.
"""
import argparse
import random
import statistics
import time
from concurrent.futures import ThreadPoolExecutor

import httpx


def virtual_user(url: str, rounds: int, idx: int) -> list[tuple[str, float, int]]:
    samples = []
    with httpx.Client(base_url=url, timeout=30) as c:
        email = f"load{idx}@scms.example.com"
        c.post("/api/v1/auth/register", json={"name": f"Load User {idx}", "email": email, "password": "Load12345"})
        t0 = time.perf_counter()
        r = c.post("/api/v1/auth/login", json={"email": email, "password": "Load12345"})
        samples.append(("login", time.perf_counter() - t0, r.status_code))
        h = {"Authorization": f"Bearer {r.json()['access_token']}"}
        cats = c.get("/api/v1/categories", headers=h).json()
        for _ in range(rounds):
            for name, method, path, body in (
                ("submit", "POST", "/api/v1/complaints", {
                    "category_id": random.choice(cats)["category_id"],
                    "priority": random.choice(["LOW", "MEDIUM", "HIGH"]),
                    "description": "Load test complaint description",
                }),
                ("list", "GET", "/api/v1/complaints?limit=20", None),
                ("notifications", "GET", "/api/v1/notifications", None),
            ):
                t0 = time.perf_counter()
                r = c.request(method, path, json=body, headers=h)
                samples.append((name, time.perf_counter() - t0, r.status_code))
                if name == "submit" and r.status_code == 201:
                    t0 = time.perf_counter()
                    r2 = c.get(f"/api/v1/complaints/{r.json()['complaint_id']}", headers=h)
                    samples.append(("detail", time.perf_counter() - t0, r2.status_code))
    return samples


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8000")
    ap.add_argument("--users", type=int, default=50)
    ap.add_argument("--rounds", type=int, default=10)
    args = ap.parse_args()
    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=args.users) as pool:
        results = [s for batch in pool.map(lambda i: virtual_user(args.url, args.rounds, i), range(args.users)) for s in batch]
    elapsed = time.perf_counter() - start
    errors = [s for s in results if s[2] >= 400]
    all_t = [s[1] for s in results]
    print(f"virtual users: {args.users}, requests: {len(results)}, errors: {len(errors)}, wall time: {elapsed:.1f}s, throughput: {len(results) / elapsed:.1f} req/s")
    print(f"{'operation':<14}{'count':>7}{'median ms':>11}{'p95 ms':>9}{'max ms':>9}")
    for name in ("login", "submit", "detail", "list", "notifications"):
        t = [s[1] * 1000 for s in results if s[0] == name]
        if t:
            p95 = statistics.quantiles(t, n=20)[-1] if len(t) > 1 else t[0]
            print(f"{name:<14}{len(t):>7}{statistics.median(t):>11.0f}{p95:>9.0f}{max(t):>9.0f}")
    overall = statistics.quantiles(all_t, n=20)[-1]
    print(f"overall p95: {overall * 1000:.0f} ms -> NFR-01 (<3000 ms for 95%): {'PASS' if overall < 3 and not errors else 'FAIL'}")


if __name__ == "__main__":
    main()
