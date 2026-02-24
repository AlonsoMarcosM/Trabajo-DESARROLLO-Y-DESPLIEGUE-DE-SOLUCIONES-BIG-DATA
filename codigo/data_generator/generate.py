"""
Synthetic Telco Churn Dataset Generator
========================================
Generates realistic customer interaction data for churn prediction with:

  context/customers.csv
      ~2.3M customers (2M base + entrances/exits over time)
      Includes churn_date (None if still active) for point-in-time joins.
      Protected attributes: age_group, gender, contract_type, region_type

  events/YYYY/MM/usage.json
      One record per active customer per month (~2M rows/month)
      Monthly aggregated usage metrics: data, calls, SMS, roaming, etc.
      Label: will_churn  (1 if the customer churns THIS month)

  events/YYYY/MM/interactions.json
      Variable volume: call-center calls, complaints, plan changes, etc.
      Multiple interaction records per customer per month are possible.

Date range: 2023-01 to 2025-06
  - 2023-2024: training period
  - 2025-01 to 2025-06: production (data drift + concept drift injected)

CHURN DESIGN (~6% monthly rate, intentionally hard to predict):
  - Churn is driven by a latent dissatisfaction score that evolves over time
  - Many loyal customers show similar surface patterns to churners
  - Concept drift in 2025: a new low-cost competitor triggers churn in previously
    stable customer segments (young + high-data-usage), breaking 2023-2024 patterns

BIAS DESIGN (domain-justified, measurable via fairness metrics):
  Group size disparity:
    - age_group: ~65% young (18-45) vs ~35% senior (46+)
    - gender: ~52% M, ~44% F, ~4% O
    - contract_type: ~55% monthly vs ~45% annual (annual churns less)
    - region_type: ~70% urban vs ~30% rural

  Prevalence disparity (domain-justified):
    - Monthly contracts churn ~3x more than annual (no lock-in)
    - Rural customers churn more (worse coverage, fewer alternatives)
    - Seniors churn less (less price-sensitive, more loyal by habit)
    - Gender: NO artificial multiplier (emerges from income/contract correlation)

  Separability disparity (organic):
    - Annual contract customers have cleaner churn signals (usage drop is sharper)
    - Monthly contract churners blend in more with normal usage variation
    -> Model will have higher FPR for monthly/rural segments
"""

import os
import json
import random
import math
import csv
import calendar
import hashlib
from datetime import datetime, timedelta, date

# =============================================================================
# DELAYED FEEDBACK HELPERS
# =============================================================================

def _gamma_delay(shape: float, scale: float, lo: int, hi: int) -> int:
    """Sample delay in days from a Gamma distribution, clamped to [lo, hi]."""
    return max(lo, min(hi, int(random.gammavariate(shape, scale))))

def _label_available_date(event_ts: str, delay_days: float = 0,
                           delay_hours: float = 0) -> str:
    """Return ISO timestamp when the label becomes available."""
    from datetime import datetime, timedelta
    dt = datetime.strptime(event_ts, "%Y-%m-%dT%H:%M:%SZ")
    dt += timedelta(days=delay_days, hours=delay_hours)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

def _end_of_month_ts(year: int, month: int) -> str:
    """Return last-day-of-month timestamp (telco batch processing)."""
    import calendar
    from datetime import datetime
    last_day = calendar.monthrange(year, month)[1]
    return datetime(year, month, last_day, 23, 59, 59).strftime("%Y-%m-%dT%H:%M:%SZ")


# --- Reproducibility ----------------------------------------------------------
SEED = 42
random.seed(SEED)

# --- Volume -------------------------------------------------------------------
BASE_CUSTOMERS      = 2_000_000   # active at any point
MONTHLY_NEW_CLIENTS = 35_000      # gross new additions per month
USAGE_ROWS_PER_MONTH = 2_000_000  # one per active customer (approx)

# --- Date range ---------------------------------------------------------------
START_YEAR, START_MONTH = 2023, 1
END_YEAR,   END_MONTH   = 2025, 6


# =============================================================================
# CHURN RATE SCHEDULE
# =============================================================================

def base_churn_rate(year: int, month: int) -> float:
    """
    Global monthly churn rate ~5-7%, with:
    - Seasonal peaks (January: new-year resolutions, September: back-to-school)
    - Slow upward trend (market saturation)
    - 2025 spike: new competitor triggers structural churn in young/data-heavy segments
    """
    base     = 0.060
    seasonal = 0.010 * math.sin(2 * math.pi * (month - 3) / 12)  # peaks Jan & Jul
    trend    = 0.002 * ((year - 2023) * 12 + (month - 1)) / 12   # slow drift up
    drift    = 0.018 if year == 2025 else 0.0                      # competitor entry
    return max(0.030, min(0.130, base + seasonal + trend + drift))


# =============================================================================
# BIAS CONFIG
# =============================================================================

AGE_GROUP_WEIGHTS   = {"young": 0.65, "senior": 0.35}
GENDER_WEIGHTS      = {"M": 0.52, "F": 0.44, "O": 0.04}
CONTRACT_WEIGHTS    = {"monthly": 0.55, "annual": 0.45}
REGION_WEIGHTS      = {"urban": 0.70, "rural": 0.30}

# Churn multipliers — domain justified
CONTRACT_CHURN_MULT = {"monthly": 1.60, "annual": 0.52}
REGION_CHURN_MULT   = {"urban": 0.88, "rural": 1.35}
AGE_CHURN_MULT      = {"young": 1.10, "senior": 0.75}

def get_churn_multiplier(contract_type, region_type, age_group):
    return (CONTRACT_CHURN_MULT[contract_type] *
            REGION_CHURN_MULT[region_type] *
            AGE_CHURN_MULT[age_group])


# =============================================================================
# HELPERS
# =============================================================================

def _clamp(v, lo, hi): return max(lo, min(hi, v))

def _gauss(mu, sigma, lo=None, hi=None):
    v = random.gauss(mu, sigma)
    if lo is not None: v = max(v, lo)
    if hi is not None: v = min(v, hi)
    return v

def _choice(seq): return seq[int(random.random() * len(seq))]

def _weighted_choice(options, weights):
    total = sum(weights)
    r, cum = random.random() * total, 0.0
    for o, w in zip(options, weights):
        cum += w
        if r <= cum: return o
    return options[-1]

def _fmt_date(d): return d.strftime("%Y-%m-%d")
def _fmt_ts(d):   return d.strftime("%Y-%m-%dT%H:%M:%SZ")

def _rand_date(start, end):
    return start + timedelta(days=int(random.random() * (end - start).days))

def _hash_id(prefix, n):
    h = hashlib.md5(f"{prefix}{n}{SEED}".encode()).hexdigest()[:12].upper()
    return f"{prefix}{h}"

def _iter_months(sy, sm, ey, em):
    y, m = sy, sm
    while (y, m) <= (ey, em):
        yield y, m
        m += 1
        if m > 12: m, y = 1, y + 1


# =============================================================================
# CUSTOMER GENERATION
# =============================================================================

TARIFF_PLANS = ["basic_10gb", "standard_30gb", "premium_100gb", "unlimited", "family_pack"]
TARIFF_W_YOUNG  = [10, 20, 30, 30, 10]
TARIFF_W_SENIOR = [30, 35, 20, 10,  5]

DEVICES = ["android_low", "android_mid", "android_high", "iphone", "other"]
DEV_W   = [20, 30, 20, 25, 5]

ACQUISITION_CHANNELS = ["online", "store", "telesales", "referral", "promotion"]
ACQ_W = [35, 25, 15, 15, 10]

REGIONS_ESP = [
    "madrid", "barcelona", "valencia", "sevilla", "bilbao",
    "rural_norte", "rural_sur", "rural_centro", "rural_este", "rural_oeste"
]

PAYMENT_METHODS = ["direct_debit", "credit_card", "bank_transfer", "digital_wallet"]
PAY_W = [55, 25, 12, 8]

INCOME_BRACKETS = ["<18k", "18k-30k", "30k-50k", "50k-80k", ">80k"]


def _sample_age_group():
    if random.random() < AGE_GROUP_WEIGHTS["young"]:
        return int(_gauss(29, 8, 18, 45)), "young"
    return int(_gauss(57, 10, 46, 85)), "senior"

def _sample_gender():
    r = random.random()
    if r < GENDER_WEIGHTS["M"]: return "M"
    if r < GENDER_WEIGHTS["M"] + GENDER_WEIGHTS["F"]: return "F"
    return "O"

def _sample_contract(age_group):
    # Seniors slightly more likely to have annual contracts
    p_monthly = 0.50 if age_group == "senior" else 0.58
    return "monthly" if random.random() < p_monthly else "annual"

def _sample_region():
    if random.random() < REGION_WEIGHTS["urban"]:
        return _choice(REGIONS_ESP[:5]), "urban"
    return _choice(REGIONS_ESP[5:]), "rural"


def generate_customers(n: int, id_offset: int = 0,
                       join_year: int = 2023, join_month: int = 1) -> list[dict]:
    """
    join_year/join_month: the calendar month these customers enter the active base.
    For the initial 2M base: (2023, 1).
    For monthly new additions: the actual month they join.
    signup_date is set to a random date within the 6-48 months BEFORE join_month
    (simulates customers who already had a contract elsewhere or are brand-new).
    """
    customers = []
    join_as_date = date(join_year, join_month, 1)
    # Historical customers signed up 6-60 months before joining our window
    signup_earliest = join_as_date - timedelta(days=60 * 30)
    signup_latest   = join_as_date - timedelta(days=1)

    for i in range(n):
        cid = _hash_id("CL", i + id_offset)

        age, age_group         = _sample_age_group()
        gender                  = _sample_gender()
        contract_type           = _sample_contract(age_group)
        region, region_type     = _sample_region()

        tariff = _weighted_choice(
            TARIFF_PLANS,
            TARIFF_W_YOUNG if age_group == "young" else TARIFF_W_SENIOR
        )
        device           = _weighted_choice(DEVICES, DEV_W)
        acq_channel      = _weighted_choice(ACQUISITION_CHANNELS, ACQ_W)
        payment_method   = _weighted_choice(PAYMENT_METHODS, PAY_W)

        # Monthly fee correlated with tariff and contract
        base_fee = {"basic_10gb": 15, "standard_30gb": 25, "premium_100gb": 40,
                    "unlimited": 55, "family_pack": 70}[tariff]
        discount = 0.10 if contract_type == "annual" else 0.0
        monthly_fee = round(base_fee * (1 - discount) * _gauss(1.0, 0.05, 0.85, 1.20), 2)

        # Num lines: family packs have more
        num_lines = int(_gauss(3.5, 1.0, 2, 6)) if tariff == "family_pack" else 1

        # Tenure at start of data window (2023-01)
        signup_date   = _rand_date(signup_earliest, signup_latest)
        tenure_months = max(1, (join_as_date - signup_date).days // 30)

        # NPS / satisfaction proxy (latent — used to shape churn probability)
        # Correlates with: contract, region, tariff, tenure
        base_nps = 6.5
        if contract_type == "annual":  base_nps += 0.8
        if region_type == "rural":     base_nps -= 1.0
        if tariff == "unlimited":      base_nps += 0.5
        if tenure_months > 36:         base_nps += 0.4
        nps_score = round(_clamp(_gauss(base_nps, 1.5, 1, 10), 1, 10), 1)

        # Latent dissatisfaction (drives churn probability evolution)
        mult = get_churn_multiplier(contract_type, region_type, age_group)
        dissatisfaction = _clamp(random.betavariate(2, max(2, int(8 / mult))), 0.0, 1.0)

        # Income bracket (correlated with tariff / age)
        if tariff in ("premium_100gb", "unlimited", "family_pack"):
            income = _weighted_choice(INCOME_BRACKETS, [5, 15, 30, 35, 15])
        else:
            income = _weighted_choice(INCOME_BRACKETS, [20, 35, 30, 12, 3])

        # Paperless & autopay correlated with digital savviness / age
        paperless = 1 if random.random() < (0.80 if age_group == "young" else 0.45) else 0
        autopay   = 1 if payment_method == "direct_debit" else 0

        # churn_date: will be filled during event generation; None = still active
        customers.append({
            # Identifiers
            "customer_id":           cid,
            "customer_updated_at":   None,      # filled on churn or plan change

            # Protected attributes
            # NOTE: age_group → Gold: CASE WHEN age <= 45 THEN 'young' ELSE 'senior'
            "age":                   age,
            "gender":                gender,
            "contract_type":         contract_type,
            "region":                region,
            "region_type":           region_type,

            # Profile
            "tariff_plan":           tariff,
            "monthly_fee":           monthly_fee,
            "num_lines":             num_lines,
            "device_type":           device,
            "acquisition_channel":   acq_channel,
            "payment_method":        payment_method,
            "signup_date":           _fmt_date(signup_date),
            "has_tv_bundle":         1 if random.random() < 0.30 else 0,
            "has_fiber":             1 if (region_type == "urban" and random.random() < 0.65) else (
                                     1 if random.random() < 0.20 else 0),
            "has_roaming":           1 if (age_group == "young" and random.random() < 0.45) else (
                                     1 if random.random() < 0.20 else 0),
            "paperless_billing":     paperless,
            "autopay":               autopay,
            "nps_score_at_start":    nps_score,
            # NOTE: income_bracket removed → Gold: business rule derived from tariff_plan
            # NOTE: churn_date / churn_reason removed from customers.csv
            #   → Silver keeps is_active flag; churn facts live in labels/data.json
            "is_active":             1,   # set to 0 on churn during simulation

            # Internal
            "_churn_date":           None,   # used for label file; not exported
            "_churn_reason":         None,
            "_dissatisfaction":      round(dissatisfaction, 6),
            "_age_group":            age_group,
            "_contract_type":        contract_type,
            "_region_type":          region_type,
            "_gender":               gender,
            "_nps":                  nps_score,
            "_active":               True,
            "_join_month":           (join_year, join_month),
            "_churn_month":          None,   # (year, month) when they churn
        })

    return customers


CHURN_REASONS = [
    "price_too_high", "better_offer_competitor", "coverage_issues",
    "poor_customer_service", "moving_abroad", "financial_difficulties",
    "family_plan_consolidation", "service_quality", "unknown"
]
REASON_W_URBAN  = [28, 25, 8,  18, 5, 7, 5,  3, 1]
REASON_W_RURAL  = [20, 15, 30, 15, 3, 8, 5,  3, 1]
# 2025: competitor reasons spike
REASON_W_2025   = [15, 45, 8,  12, 3, 5, 5,  5, 2]


# =============================================================================
# USAGE RECORD GENERATION
# =============================================================================

def _data_gb(tariff, age_group, is_churn_month, month_offset):
    """Monthly data consumption in GB. Churners show drop in last 1-2 months."""
    caps = {
        "basic_10gb": (6, 3), "standard_30gb": (22, 6),
        "premium_100gb": (65, 20), "unlimited": (95, 30), "family_pack": (80, 25)
    }
    mu, sigma = caps.get(tariff, (20, 8))
    if age_group == "senior": mu *= 0.55
    # Pre-churn drop: consumption decreases in the months before leaving
    if is_churn_month:    mu *= _gauss(0.55, 0.15, 0.25, 0.80)
    elif month_offset == 1: mu *= _gauss(0.78, 0.10, 0.55, 0.95)   # month before churn
    return round(max(0.1, _gauss(mu, sigma)), 2)

def _call_minutes(age_group, is_churn_month):
    mu = 180 if age_group == "senior" else 90
    if is_churn_month: mu *= _gauss(0.65, 0.15, 0.30, 0.90)
    return int(max(0, _gauss(mu, mu * 0.4)))

def _sms_count(age_group, is_churn_month):
    mu = 15 if age_group == "senior" else 40
    if is_churn_month: mu *= _gauss(0.70, 0.15, 0.30, 0.95)
    return int(max(0, _gauss(mu, mu * 0.5)))

def _roaming_gb(has_roaming, month):
    # Peaks in summer (June-August)
    if not has_roaming: return 0.0
    seasonal = 1.0 + 0.8 * max(0, math.sin(2 * math.pi * (month - 3) / 12))
    return round(max(0.0, _gauss(1.5 * seasonal, 0.8)), 2)


def build_usage_record(customer: dict, year: int, month: int,
                        tenure_months: int, month_offset: int,
                        active_days: int = None) -> dict:
    """
    month_offset : months until churn (0 = churn month, 1 = one month before).
                   None if not churning in the window.
    active_days  : days the customer was active this month. Full month if None.
                   Used to pro-rate consumption on the churn month (e.g. churn
                   on day 5 → only 5 days of data/calls/SMS/bill).
    """
    is_churn_month = (month_offset == 0)
    days_in_month  = calendar.monthrange(year, month)[1]
    active_days    = active_days if active_days is not None else days_in_month
    day_ratio      = active_days / days_in_month   # 1.0 for non-churn months

    ag     = customer["_age_group"]
    ct     = customer["_contract_type"]
    rt     = customer["_region_type"]
    tariff = customer["tariff_plan"]
    nps    = customer["_nps"]

    # Generate full-month consumption then scale to active days
    data_gb   = round(_data_gb(tariff, ag, is_churn_month, month_offset if month_offset else 99) * day_ratio, 2)
    calls_min = round(_call_minutes(ag, is_churn_month) * day_ratio)
    sms       = round(_sms_count(ag, is_churn_month) * day_ratio)
    roaming   = round(_roaming_gb(customer["has_roaming"], month) * day_ratio, 2)

    # Bill is pro-rated to active days; overage only if used the service
    base_fee   = round(customer["monthly_fee"] * day_ratio, 2)
    overage    = round(max(0.0, _gauss(0, 3, 0, 30)), 2) if (random.random() < 0.15 and active_days > 5) else 0.0
    bill_amount = round(base_fee + overage, 2)

    # Payment behaviour: late payments increase near churn
    days_late = 0
    if is_churn_month and random.random() < 0.35:
        days_late = int(_gauss(12, 6, 1, 45))
    elif month_offset and month_offset <= 2 and random.random() < 0.15:
        days_late = int(_gauss(5, 3, 1, 20))

    # NPS drift: satisfaction erodes in months before churn
    nps_this_month = nps
    if month_offset is not None:
        nps_drop = max(0, (3 - month_offset)) * _gauss(0.8, 0.3, 0, 2)
        nps_this_month = round(_clamp(nps - nps_drop, 1, 10), 1)

    # Coverage quality: worse in rural, random outages
    coverage_score = round(_gauss(
        7.5 if rt == "urban" else 5.5, 1.2, 1, 10), 1)

    # Speed test (Mbps download) — correlated with fiber and region
    has_fiber = customer["has_fiber"]
    speed_mbps = round(_gauss(
        300 if has_fiber else 25,
        80  if has_fiber else 12,
        2, 1000
    ), 1)

    return {
        "customer_id":           customer["customer_id"],
        "year_month":            f"{year}-{month:02d}",
        # NOTE: tenure_months removed → Gold: datediff(year_month, signup_date) via JOIN
        # NOTE: num_services removed → Gold: 1 + has_tv_bundle + has_fiber + has_roaming via JOIN
        # NOTE: contract_type, region_type removed → Gold: point-in-time JOIN with customers.csv
        "days_active":           active_days,
        "tariff_plan":           tariff,   # kept: changes dynamically (2025 drift); no contracts table
        "data_consumed_gb":      data_gb,
        "call_minutes":          calls_min,
        "sms_count":             sms,
        "roaming_gb":            roaming,
        "bill_amount":           bill_amount,
        "bill_overage":          overage,
        "days_payment_late":     days_late,
        "coverage_score":        coverage_score,
        "speed_mbps":            speed_mbps,
        "nps_score":             nps_this_month,
        # Internal — used by inject_2025_drift; not exported
        "_tenure_months":        tenure_months,
    }


# =============================================================================
# INTERACTION RECORD GENERATION
# =============================================================================

INTERACTION_TYPES = [
    "call_center_inquiry", "call_center_complaint", "online_chat",
    "store_visit", "plan_upgrade", "plan_downgrade", "plan_renewal",
    "technical_support", "billing_dispute", "cancellation_request",
    "loyalty_offer_accepted", "loyalty_offer_rejected", "port_out_request"
]

INTERACTION_W_NORMAL = [20, 8, 15, 8, 6, 4, 5, 12, 5, 1, 5, 3, 1]
INTERACTION_W_CHURN  = [10, 18, 8, 6, 2, 8, 2, 10, 15, 12, 3, 10, 6]

RESOLUTION = ["resolved_first_contact", "escalated", "unresolved", "callback_scheduled"]
RES_W      = [55, 20, 15, 10]


def build_interaction_records(customer: dict, year: int, month: int,
                               month_offset, active_days: int = None) -> list[dict]:
    """
    Returns 0-N interaction records for a customer in a given month.
    Churners generate more interactions, especially complaints and cancellations.
    active_days: caps the day range for timestamps in the churn month.
    """
    is_churn_month  = (month_offset == 0)
    pre_churn_close = (month_offset is not None and month_offset <= 2)
    days_in_month   = calendar.monthrange(year, month)[1]
    max_day         = active_days if active_days is not None else days_in_month

    # Number of interactions this month
    if is_churn_month:
        n_interactions = int(abs(_gauss(2.8, 1.5, 1, 8)))
    elif pre_churn_close:
        n_interactions = int(abs(_gauss(1.8, 1.2, 0, 5)))
    else:
        n_interactions = 1 if random.random() < 0.30 else 0

    if n_interactions == 0:
        return []

    records = []
    days_in_month = calendar.monthrange(year, month)[1]

    weights = INTERACTION_W_CHURN if (is_churn_month or pre_churn_close) else INTERACTION_W_NORMAL

    for _ in range(n_interactions):
        itype = _weighted_choice(INTERACTION_TYPES, weights)
        day   = int(random.random() * max_day) + 1
        hour  = int(_gauss(11, 3, 8, 20))
        ts    = datetime(year, month, day, hour,
                         int(random.random() * 60), int(random.random() * 60))
        channel = _choice(["phone", "phone", "app", "web", "store"])
        duration_sec = int(_gauss(320, 180, 30, 2400)) if "call" in itype else None
        resolution = _weighted_choice(RESOLUTION, RES_W) if "complaint" in itype or "dispute" in itype else None

        records.append({
            "customer_id":       customer["customer_id"],
            "timestamp":         _fmt_ts(ts),
            # NOTE: year_month removed → Gold: date_format(timestamp, 'yyyy-MM')
            # NOTE: contract_type, region_type removed → Gold: point-in-time JOIN with customers.csv
            "interaction_type":  itype,
            "channel":           channel,
            "duration_seconds":  duration_sec,
            "resolution":        resolution,
            "agent_id":          _hash_id("AG", int(random.random() * 500)),
            "satisfaction_score": round(_clamp(_gauss(
                3.2 if is_churn_month else 4.1, 1.2, 1, 5), 1, 5), 1),
        })

    return records


# =============================================================================
# 2025 DRIFT INJECTION
# =============================================================================

def inject_2025_drift(usage: dict, customer: dict, year: int, month: int) -> dict:
    """
    Data drift:
      - New tariff plans appear (esim_only, 5g_premium) -> new values in tariff_plan
      - Bill format changes: digital_discount field appears
      - Speed measurements in new units occasionally

    Concept drift:
      - Young + high-data customers now churn at much higher rates due to new competitor
        (pattern inversion: high data usage was previously a RETENTION signal;
         in 2025 it signals churn for young segments)
      - Long-tenure customers start churning (previously most stable segment)
    """
    # Data drift: new tariff labels
    if customer["_age_group"] == "young" and random.random() < 0.12:
        usage["tariff_plan"] = _choice(["esim_only_20gb", "5g_premium_unlimited"])

    # Data drift: new billing field (appears gradually from month 2)
    if month >= 2:
        usage["digital_discount"] = round(_gauss(2.5, 1.0, 0, 8), 2) if random.random() < 0.40 else 0.0

    # Concept drift: high data usage + young now predicts churn (competitor offers better data deals)
    if customer["_age_group"] == "young" and usage["data_consumed_gb"] > 50:
        if random.random() < 0.22:
            customer["_churn_override"] = (year, month)  # concept drift: force churn this month

    # Concept drift: long-tenure customers start churning (loyalty no longer sticky)
    tenure = usage["_tenure_months"]
    if tenure > 48 and random.random() < 0.08:
        customer["_churn_override"] = (year, month)  # concept drift: long-tenure churn

    return usage


# =============================================================================
# ORCHESTRATION
# =============================================================================

def main():
    base_dir    = os.path.dirname(os.path.abspath(__file__))
    events_dir        = os.path.join(base_dir, "events")
    source_buffer_dir = os.path.join(base_dir, "source_buffer")
    context_dir = os.path.join(base_dir, "context")
    os.makedirs(context_dir, exist_ok=True)

    # ── 1. Generate initial customer base ─────────────────────────────────────
    print("=" * 65)
    print("STEP 1: Generating customer base")
    print("=" * 65)
    customers = generate_customers(BASE_CUSTOMERS, id_offset=0)
    next_id_offset = BASE_CUSTOMERS

    # ── 2. Month-by-month simulation ──────────────────────────────────────────
    print("\n" + "=" * 65)
    print("STEP 2: Monthly simulation (2023-2025)")
    print("=" * 65)

    all_months = list(_iter_months(START_YEAR, START_MONTH, END_YEAR, END_MONTH))
    month_index = {(y, m): i for i, (y, m) in enumerate(all_months)}

    # Pre-assign churn months to each customer (makes pre-churn signal generation easier)
    # We simulate each customer's churn month probabilistically across the full window
    print("  Pre-assigning churn schedules...")

    def assign_churn(c):
        """Assign a churn month for a customer, starting from their _join_month."""
        mult = get_churn_multiplier(c["_contract_type"], c["_region_type"], c["_age_group"])
        monthly_p = _clamp(0.060 * mult * (0.5 + c["_dissatisfaction"] * 3), 0.005, 0.20)
        join_ym = c["_join_month"]
        churn_ym = None
        for (y, m) in all_months:
            if (y, m) < join_ym:
                continue   # customer hasn't joined yet
            effective_p = monthly_p * (1.30 if y == 2025 else 1.0)
            if random.random() < effective_p:
                churn_ym = (y, m)
                break
        c["_churn_month"] = churn_ym

    for c in customers:
        assign_churn(c)

    total_usage_rows   = 0
    total_interactions = 0
    total_churns       = 0
    new_customers_pool = []

    for yi, (year, month) in enumerate(all_months):
        is_2025  = (year == 2025)
        base_out = source_buffer_dir if year == 2025 else events_dir

        usage_records   = []
        interact_records = []
        churned_this_month = 0

        # Add new customers joining this month
        new_batch = generate_customers(
            MONTHLY_NEW_CLIENTS, id_offset=next_id_offset,
            join_year=year, join_month=month
        )
        next_id_offset += MONTHLY_NEW_CLIENTS
        for c in new_batch:
            assign_churn(c)
        customers.extend(new_batch)

        # Process all active customers
        for c in customers:
            if not c["_active"]: continue
            if c["_join_month"] > (year, month): continue   # not yet joined

            churn_ym  = c["_churn_month"]
            is_churn  = (churn_ym == (year, month))

            # month_offset: how many months until churn (None = not churning in window)
            if churn_ym is not None:
                idx_now   = month_index.get((year, month), 0)
                idx_churn = month_index.get(churn_ym, 0)
                month_offset = idx_churn - idx_now
                if month_offset < 0: month_offset = None   # churn already passed
            else:
                month_offset = None

            # Tenure at this month
            signup     = date.fromisoformat(c["signup_date"])
            tenure_now = max(1, (date(year, month, 1) - signup).days // 30)

            # If churning this month, determine the exact churn day FIRST
            # so we can pro-rate usage and cap interaction timestamps correctly
            active_days = None
            if is_churn:
                days_in_month = calendar.monthrange(year, month)[1]
                churn_day     = int(random.random() * days_in_month) + 1
                active_days   = churn_day   # customer was active for churn_day days
                churn_date    = date(year, month, churn_day)
                rw = REASON_W_2025 if is_2025 else (
                     REASON_W_RURAL if c["_region_type"] == "rural" else REASON_W_URBAN)
                churn_reason  = _weighted_choice(CHURN_REASONS, rw)
                c["_active"]           = False
                c["_churn_date"]       = _fmt_date(churn_date)
                c["is_active"]          = 0
                c["_churn_reason"]     = churn_reason
                c["customer_updated_at"] = _fmt_ts(
                    datetime(churn_date.year, churn_date.month, churn_date.day, 12, 0)
                )
                churned_this_month += 1

            # Usage record — pro-rated to active_days on churn month
            usage = build_usage_record(c, year, month, tenure_now, month_offset,
                                       active_days=active_days)
            if is_2025:
                usage = inject_2025_drift(usage, c, year, month)
                # Concept drift may have forced a churn override — update churn schedule
                if c.get("_churn_override") == (year, month) and not is_churn:
                    c["_churn_month"] = (year, month)
                    churn_ym  = (year, month)
                    is_churn  = True
                    # Pro-rate retroactively for the drift-forced churn
                    days_in_month = calendar.monthrange(year, month)[1]
                    churn_day   = int(random.random() * days_in_month) + 1
                    active_days = churn_day
                    churn_date  = date(year, month, churn_day)
                    usage["days_active"]      = active_days
                    usage["data_consumed_gb"] = round(usage["data_consumed_gb"] * active_days / days_in_month, 2)
                    usage["call_minutes"]     = round(usage["call_minutes"]     * active_days / days_in_month)
                    usage["sms_count"]        = round(usage["sms_count"]        * active_days / days_in_month)
                    usage["bill_amount"]      = round(usage["bill_amount"]      * active_days / days_in_month, 2)
                    rw = REASON_W_2025
                    c["_active"]           = False
                    c["_churn_date"]       = _fmt_date(churn_date)
                    c["is_active"]         = 0
                    c["_churn_reason"]     = _weighted_choice(CHURN_REASONS, rw)
                    c["customer_updated_at"] = _fmt_ts(
                        datetime(churn_date.year, churn_date.month, churn_date.day, 12, 0)
                    )
                    churned_this_month += 1
            usage_records.append(usage)

            # Interaction records — timestamps capped to active_days
            inter = build_interaction_records(c, year, month, month_offset,
                                              active_days=active_days)
            interact_records.extend(inter)

        total_usage_rows   += len(usage_records)
        total_interactions += len(interact_records)
        total_churns       += churned_this_month
        active_count        = sum(1 for c in customers if c["_active"])
        churn_rate_obs      = churned_this_month / max(len(usage_records), 1)

        print(f"  [{year}-{month:02d}]  active={active_count:,}  "
              f"churned={churned_this_month:,} ({churn_rate_obs:.2%})  "
              f"interactions={len(interact_records):,}")

        # Write usage
        usage_event_dir = os.path.join(base_out, "usage", str(year), f"{month:02d}")
        usage_label_dir = os.path.join(base_out, "labels", str(year), f"{month:02d}")
        inter_event_dir = os.path.join(base_out, "interactions", str(year), f"{month:02d}")
        os.makedirs(usage_event_dir, exist_ok=True)
        os.makedirs(usage_label_dir, exist_ok=True)
        os.makedirs(inter_event_dir, exist_ok=True)

        # usage: no timestamp, sorted by year_month (all same within a file)
        with open(os.path.join(usage_event_dir, "data.json"), "w", encoding="utf-8") as f:
            for r in usage_records:
                row = {k: v for k, v in r.items() if not k.startswith("_")}
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        # churn label available at end of month (batch admin process)
        label_ts = _end_of_month_ts(year, month)
        churn_lookup = {c["customer_id"]: c.get("_churn_date") for c in customers}
        label_records = [{
            "customer_id": r["customer_id"],
            "year_month":  r["year_month"],
            "churn_date":  churn_lookup.get(r["customer_id"]),
            "label_available_date": label_ts,
        } for r in usage_records]
        label_records.sort(key=lambda x: x["label_available_date"])
        with open(os.path.join(usage_label_dir, "data.json"), "w", encoding="utf-8") as f:
            for rec in label_records:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

        # interactions: have timestamps, sort and strip no label needed
        interact_records.sort(key=lambda x: x["timestamp"])
        with open(os.path.join(inter_event_dir, "data.json"), "w", encoding="utf-8") as f:
            for r in interact_records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # ── 3. Write customers.csv ─────────────────────────────────────────────────
    print("\n" + "=" * 65)
    print("STEP 3: Writing customers.csv")
    print("=" * 65)

    export_fields = [k for k in customers[0].keys() if not k.startswith("_")]
    customers_path = os.path.join(context_dir, "customers.csv")
    with open(customers_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=export_fields)
        writer.writeheader()
        for c in customers:
            writer.writerow({k: c[k] for k in export_fields})

    total_customers = len(customers)
    n_senior   = sum(1 for c in customers if c["_age_group"] == "senior")
    n_other    = sum(1 for c in customers if c["_gender"] == "O")
    n_monthly  = sum(1 for c in customers if c["_contract_type"] == "monthly")
    n_rural    = sum(1 for c in customers if c["_region_type"] == "rural")
    n_churned  = sum(1 for c in customers if c["_churn_date"] is not None)

    print(f"  {total_customers:,} customers written to {customers_path}")

    print("\n" + "=" * 65)
    print("SUMMARY")
    print("=" * 65)
    print(f"  Total customers    : {total_customers:,}")
    print(f"  Total churned      : {n_churned:,} ({n_churned/total_customers:.1%})")
    print(f"  Total usage rows   : {total_usage_rows:,}")
    print(f"  Total interactions : {total_interactions:,}")
    print()
    print("  Group size disparity:")
    print(f"    age_group   : young={total_customers-n_senior:,} "
          f"({(total_customers-n_senior)/total_customers:.1%}) | "
          f"senior={n_senior:,} ({n_senior/total_customers:.1%})")
    print(f"    gender      : M~{GENDER_WEIGHTS['M']:.0%} | F~{GENDER_WEIGHTS['F']:.0%} | "
          f"O={n_other:,} ({n_other/total_customers:.1%})")
    print(f"    contract    : monthly={n_monthly:,} ({n_monthly/total_customers:.1%}) | "
          f"annual={total_customers-n_monthly:,} ({(total_customers-n_monthly)/total_customers:.1%})")
    print(f"    region      : urban={total_customers-n_rural:,} "
          f"({(total_customers-n_rural)/total_customers:.1%}) | "
          f"rural={n_rural:,} ({n_rural/total_customers:.1%})")
    print()
    print("  Bias (domain-justified):")
    print("    Prevalence disparity -> contract_type x region_type x age_group")
    print("    Separability (organic) -> annual contracts have sharper pre-churn")
    print("      usage drops; rural/monthly blend with normal variation")
    print()
    print("  2025 drifts:")
    print("    Data drift    -> new tariffs (esim_only, 5g_premium), digital_discount field")
    print("    Concept drift -> young+high-data now churns (competitor); long-tenure churns")
    print()
    print("  Output:")
    print("    context/customers.csv")
    print("    events/YYYY/MM/usage.json")
    print("    events/YYYY/MM/interactions.json")
    print("\nDone!")


if __name__ == "__main__":
    main()
