# data_pipeline/crawl_and_prepare.py

"""
Harvest PR diffs + review comments (GitHub REST) and CodeReview-SE answers,
then write data/train.jsonl (fields: code, review).

Usage:
  python crawl_and_prepare.py --token <GITHUB_PAT> [--pages 5]
  
Notes:
  • We relaxed the length thresholds (diff > 80 chars, review > 15 chars).
  • We increased per-repo cap to 150.
  • We fetch both inline PR comments and top‐level issue comments.
  • We expanded the repo list to include projects with active human reviews.
"""

import argparse
import json
import time
from pathlib import Path
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin

OUT_DIR = Path("../data")
OUT_DIR.mkdir(exist_ok=True, parents=True)


def gh_pull_pairs(token: str, repo: str, per_repo: int = 150):
    """
    Return list[{code, review}] for <repo>, using REST diff endpoint.
    We relax diff length > 80 and review length > 15.
    """
    hdr_json = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }
    pulls_url = f"https://api.github.com/repos/{repo}/pulls?state=closed&per_page={per_repo}"
    try:
        pulls = requests.get(pulls_url, headers=hdr_json, timeout=30).json()
    except Exception as e:
        print(f"[❌]  {repo}: cannot list PRs → {e}")
        return []

    pairs = []
    for pr in pulls:
        if not pr.get("merged_at"):
            continue  # only merged PRs

        num = pr["number"]

        # Fetch diff
        diff_hdr = hdr_json.copy()
        diff_hdr["Accept"] = "application/vnd.github.v3.diff"
        try:
            diff = requests.get(
                f"https://api.github.com/repos/{repo}/pulls/{num}",
                headers=diff_hdr, timeout=30
            ).text
        except Exception as e:
            print(f"[skip] {repo} PR #{num}: diff fetch error → {e}")
            continue

        # Fetch inline PR review comments
        try:
            revs_code = requests.get(
                f"https://api.github.com/repos/{repo}/pulls/{num}/comments",
                headers=hdr_json, timeout=30
            ).json()
        except Exception as e:
            revs_code = []
            print(f"[skip] {repo} PR #{num}: inline comments fetch error → {e}")

        # Fetch top-level issue comments
        try:
            revs_issue = requests.get(
                f"https://api.github.com/repos/{repo}/issues/{num}/comments",
                headers=hdr_json, timeout=30
            ).json()
        except Exception as e:
            revs_issue = []
            print(f"[skip] {repo} PR #{num}: issue comments fetch error → {e}")

        all_revs = (revs_code if isinstance(revs_code, list) else []) + \
                   (revs_issue if isinstance(revs_issue, list) else [])
        review_txt = "\n".join(r.get("body", "") for r in all_revs if r.get("body"))

        if len(diff) > 80 and len(review_txt) > 15:
            pairs.append({
                "code": diff[:4000].strip(),
                "review": review_txt[:1500].strip()
            })

        if len(pairs) >= per_repo:
            break

        time.sleep(0.5)  # gentle on the API

    print(f"[✓]  {repo}: {len(pairs)} pairs")
    return pairs


def scrape_codereview(max_pages: int = 5):
    """
    Scrape CodeReview.StackExchange for code-review Q&A pairs.
    Fixed URL-joining and relaxed no-threshold; we still require review > 30 chars.
    """
    base = "https://codereview.stackexchange.com"
    pairs = []

    for page in range(1, max_pages + 1):
        try:
            soup = BeautifulSoup(
                requests.get(f"{base}/questions?tab=votes&page={page}", timeout=20).text,
                "html.parser"
            )
        except Exception as e:
            print(f"[❌]  SE list page {page} error: {e}")
            continue

        links = [a["href"] for a in soup.select("a.question-hyperlink")]
        for href in links:
            url = href if href.startswith("http") else urljoin(base, href)
            try:
                html_page = requests.get(url, timeout=20).text
            except Exception as e:
                print(f"[skip] SE question fetch error: {e}")
                continue

            s = BeautifulSoup(html_page, "html.parser")
            code = "\n".join(c.get_text() for c in s.select("pre code"))[:2000].strip()
            ans = s.select_one("div.answercell div.js-post-body")
            if code and ans:
                review = re.sub(r"\s+", " ", ans.get_text())[:1500].strip()
                if len(review) > 30:
                    pairs.append({"code": code, "review": review})

            time.sleep(1)

    print(f"[✓]  CodeReview.SE: {len(pairs)} pairs")
    return pairs


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", required=True, help="GitHub Personal Access Token")
    parser.add_argument("--pages", type=int, default=5, help="SE pages to scrape")
    args = parser.parse_args()

    dataset = []

    # Expanded list of repos with active human review
    repos = [
        "pandas-dev/pandas",
        "scikit-learn/scikit-learn",
        "tiangolo/fastapi",
        "psf/requests",
        "pytest-dev/pytest",
        "ansible/ansible",
    ]
    for r in repos:
        dataset += gh_pull_pairs(args.token, r, per_repo=150)

    # Scrape CodeReview.SE
    dataset += scrape_codereview(args.pages)

    # Save to JSONL
    out_file = OUT_DIR / "train.jsonl"
    with out_file.open("w", encoding="utf-8") as f:
        for obj in dataset:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")
    print(f"\n✅  Saved {len(dataset)} records → {out_file.resolve()}")
