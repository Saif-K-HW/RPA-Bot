"""
VYB Proactive Marketing Campaign Bot
====================================
Automated campaign assignment bot for VYB fashion eCommerce.
Reads the Task 1 customer dataset, validates data, applies proactive
marketing campaign rules, and generates output files for the marketing team.

Author:  Saif Khalifa
Course:  F21EC - e-Commerce Technology
"""

from __future__ import annotations

import csv
import os
from collections import Counter
from typing import Dict, List, Tuple


# Configuration
INPUT_FILE = "customers.csv"
OUTPUT_DIR = "output"
OUTPUT_CAMPAIGN = os.path.join(OUTPUT_DIR, "campaign_output.csv")
OUTPUT_SUMMARY = os.path.join(OUTPUT_DIR, "campaign_summary.csv")
OUTPUT_ERRORS = os.path.join(OUTPUT_DIR, "campaign_errors.csv")

# Required input fields needed for the bot to run its own logic independently.
REQUIRED_COLUMNS = [
    "Customer ID",
    "Preferred Category",
    "Purchase Frequency",
    "Avg Spend (AED)",
    "Days Since Last Purchase",
    "Loyalty Points",
    "Visits",
    "Wishlist",
    "Coupon Response",
    "Channel",
    "Recent Purchase",
]


# Validation and data loading helpers
def validate_columns(header_row: List[str]) -> None:
    """
    Validate input file structure
    Check that every required column is present in the CSV header
    """
    missing = [col for col in REQUIRED_COLUMNS if col not in header_row]
    if missing:
        raise ValueError(
            f"Missing required columns in input file: {', '.join(missing)}"
        )
    print("[OK] All required columns found in input file.")


def load_customers(filepath: str) -> List[Dict[str, str]]:
    """
    Load source dataset
    Read the CSV and return a list of dictionaries, one per customer row
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"Input file '{filepath}' not found. "
            "Please place customers.csv in the same directory as this script."
        )

    with open(filepath, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames or []
        validate_columns(header)
        rows = list(reader)

    print(f"[OK] Loaded {len(rows)} customer records from '{filepath}'.")
    return rows


def clean_value(value: object) -> str:
    """
    Normalize input value
    Strip whitespace and safely convert empty or missing values to strings
    """
    if value is None:
        return ""
    return str(value).strip()


def is_valid_row(row: Dict[str, str]) -> Tuple[bool, str]:
    """
    Validate one customer record
    Return (True, '') if the row has all critical fields populated and valid,
    otherwise return (False, reason)
    """
    cid = clean_value(row.get("Customer ID", ""))
    freq = clean_value(row.get("Purchase Frequency", ""))
    spend = clean_value(row.get("Avg Spend (AED)", ""))
    days = clean_value(row.get("Days Since Last Purchase", ""))
    loyalty = clean_value(row.get("Loyalty Points", ""))
    visits = clean_value(row.get("Visits", ""))

    if not cid:
        return False, "Missing Customer ID"
    if freq not in ("High", "Medium", "Low"):
        return False, f"Invalid or missing Purchase Frequency: '{freq}'"

    try:
        float(spend)
    except ValueError:
        return False, f"Invalid Avg Spend (AED): '{spend}'"

    try:
        int(days)
    except ValueError:
        return False, f"Invalid Days Since Last Purchase: '{days}'"

    try:
        int(loyalty)
    except ValueError:
        return False, f"Invalid Loyalty Points: '{loyalty}'"

    try:
        int(visits)
    except ValueError:
        return False, f"Invalid Visits: '{visits}'"

    return True, ""



# Scoring logic
def calculate_scores(row: Dict[str, str]) -> Dict[str, int]:
    """
    Calculate campaign support scores
    Generate VIP, Discount, and Win-Back scores for a customer row
    """
    freq = clean_value(row.get("Purchase Frequency", ""))
    spend = float(clean_value(row.get("Avg Spend (AED)", "0")))
    loyalty = int(clean_value(row.get("Loyalty Points", "0")))
    coupon = clean_value(row.get("Coupon Response", ""))
    days = int(clean_value(row.get("Days Since Last Purchase", "0")))

    vip = 0
    if freq == "High":
        vip += 1
    if spend > 800:
        vip += 1
    if loyalty > 1000:
        vip += 1

    discount = 0
    if coupon == "High":
        discount += 1
    if freq == "Medium":
        discount += 1

    winback = 0
    if freq == "Low":
        winback += 1
    if days >= 45:
        winback += 1

    return {"vip": vip, "discount": discount, "winback": winback}



# Campaign assignment
def assign_campaign(row: Dict[str, str], scores: Dict[str, int]) -> str:
    """
    Apply proactive marketing rules
    Evaluate customer data in priority order and return one campaign type
    """
    freq = clean_value(row.get("Purchase Frequency", ""))
    spend = float(clean_value(row.get("Avg Spend (AED)", "0")))
    loyalty = int(clean_value(row.get("Loyalty Points", "0")))
    coupon = clean_value(row.get("Coupon Response", ""))
    days = int(clean_value(row.get("Days Since Last Purchase", "0")))
    wishlist = clean_value(row.get("Wishlist", ""))
    visits = int(clean_value(row.get("Visits", "0")))

    vip_score = scores["vip"]

    # High-frequency customers
    if freq == "High":
        if vip_score == 3:
            return "VIP Early Access"
        if vip_score == 2:
            return "Premium Recommendation"
        return "Early Access"

    # Medium-frequency customers
    if freq == "Medium":
        if coupon == "High":
            return "10% Discount"
        if spend > 550 or loyalty > 800:
            return "Early Access"
        if wishlist not in ("None", "") and visits >= 12 and spend >= 500:
            return "Wishlist Reminder"
        return "Bundle Offer"

    # Low-frequency customers
    if freq == "Low":
        if days >= 45:
            return "Win-Back Offer"
        return "Win-Back Offer"

    return "Bundle Offer"


# Human-readable text helpers
CAMPAIGN_ACTIONS = {
    "VIP Early Access": "Send VIP early access message",
    "Premium Recommendation": "Send premium recommendation message",
    "Early Access": "Send early access message",
    "10% Discount": "Send 10% discount offer",
    "Wishlist Reminder": "Send wishlist reminder",
    "Bundle Offer": "Send bundle offer",
    "Win-Back Offer": "Send win-back promotion",
}


def create_action_text(campaign: str) -> str:
    """
    Create action message
    Return the suggested marketing action for the assigned campaign
    """
    return CAMPAIGN_ACTIONS.get(campaign, "Send marketing message")


def create_reason_text(campaign: str, scores: Dict[str, int]) -> str:
    """
    Create business explanation
    Generate a short human-readable reason for the assigned campaign
    """
    reasons = {
        "VIP Early Access": "High value and high loyalty customer",
        "Premium Recommendation": "Strong customer profile just below VIP threshold",
        "Early Access": "Active customer suitable for early access",
        "10% Discount": "Medium engagement with strong coupon response",
        "Wishlist Reminder": "Strong wishlist interest and browsing activity",
        "Bundle Offer": "Medium engagement suitable for bundle promotion",
        "Win-Back Offer": "Low activity and long purchase gap",
    }
    return reasons.get(campaign, "General marketing outreach")



# Output writers
def save_campaign_output(results: List[Dict[str, object]], filepath: str) -> None:
    """
    Save detailed campaign file
    Write the main customer-level campaign output CSV
    """
    fieldnames = [
        "Customer ID",
        "Assigned Campaign Type",
        "Preferred Delivery Channel",
        "Suggested Campaign Action",
        "VIP Score",
        "Discount Score",
        "Win-Back Score",
        "Reason",
        "Status",
        "Matches Task 1 Recommendation",
    ]
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow(r)

    print(f"[OK] Campaign output saved to '{filepath}' ({len(results)} rows).")


def save_summary_output(results: List[Dict[str, object]], filepath: str) -> Counter:
    """
    Save campaign totals
    Write summary counts by campaign type and return the count object
    """
    counts = Counter(r["Assigned Campaign Type"] for r in results)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Campaign Type", "Customer Count"])
        writer.writeheader()
        for campaign, count in sorted(counts.items()):
            writer.writerow({"Campaign Type": campaign, "Customer Count": count})

    print(f"[OK] Campaign summary saved to '{filepath}'.")
    return counts


def save_error_output(errors: List[Dict[str, str]], filepath: str) -> None:
    """
    Save invalid rows
    Write records with validation issues into a separate error log CSV
    """
    fieldnames = ["Customer ID", "Error Description"]
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for e in errors:
            writer.writerow(e)

    print(f"[OK] Error log saved to '{filepath}' ({len(errors)} rows).")


# Terminal summary
def count_task1_matches(results: List[Dict[str, object]]) -> int:
    """
    Count alignment with Task 1
    Return the number of bot-generated campaign decisions that match Task 1
    """
    return sum(1 for row in results if row["Matches Task 1 Recommendation"] == "Yes")


def print_summary(
    total: int,
    success: int,
    error_count: int,
    counts: Counter,
    task1_matches: int,
) -> None:
    """
    Print execution summary
    Display a clean terminal summary of processing results and output paths
    """
    print()
    print("=" * 60)
    print("  VYB PROACTIVE MARKETING CAMPAIGN BOT - RUN SUMMARY")
    print("=" * 60)
    print(f"  Total rows processed     : {total}")
    print(f"  Successful assignments   : {success}")
    print(f"  Error rows               : {error_count}")
    print(f"  Matches Task 1           : {task1_matches}")
    print("-" * 60)
    print("  Campaign Breakdown:")
    for campaign, count in sorted(counts.items()):
        print(f"    {campaign:<30s} : {count}")
    print("-" * 60)
    print("  Output files:")
    print(f"    - {OUTPUT_CAMPAIGN}")
    print(f"    - {OUTPUT_SUMMARY}")
    print(f"    - {OUTPUT_ERRORS}")
    print("=" * 60)
    print()


# Pipeline entry point
def main() -> None:
    """
    Pipeline Entry Point
    Loads the Task 1 dataset, validates records, applies campaign rules,
    writes output files, and prints a final terminal summary
    """
    print()
    print("=" * 60)
    print("  VYB Proactive Marketing Campaign Bot")
    print("  Fashion eCommerce - Automated Campaign Assignment")
    print("=" * 60)
    print()

    # Ensure output location exists before saving results.
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # load and validate source data.
    customers = load_customers(INPUT_FILE)

    # process each customer record independently.
    results: List[Dict[str, object]] = []
    errors: List[Dict[str, str]] = []

    for row in customers:
        cid = clean_value(row.get("Customer ID", "unknown"))

        valid, error_msg = is_valid_row(row)
        if not valid:
            errors.append({"Customer ID": cid, "Error Description": error_msg})
            continue

        scores = calculate_scores(row)
        campaign = assign_campaign(row, scores)

        # comparison against the Task 1 manually assigned campaign.
        task1 = clean_value(row.get("Recommended Campaign", ""))
        match = "Yes" if task1 and campaign == task1 else "No"

        results.append({
            "Customer ID": cid,
            "Assigned Campaign Type": campaign,
            "Preferred Delivery Channel": clean_value(row.get("Channel", "")),
            "Suggested Campaign Action": create_action_text(campaign),
            "VIP Score": scores["vip"],
            "Discount Score": scores["discount"],
            "Win-Back Score": scores["winback"],
            "Reason": create_reason_text(campaign, scores),
            "Status": "Ready for review",
            "Matches Task 1 Recommendation": match,
        })

    # save all outputs.
    save_campaign_output(results, OUTPUT_CAMPAIGN)
    counts = save_summary_output(results, OUTPUT_SUMMARY)
    save_error_output(errors, OUTPUT_ERRORS)

    # print execution summary.
    task1_matches = count_task1_matches(results)
    print_summary(len(customers), len(results), len(errors), counts, task1_matches)


if __name__ == "__main__":
    main()