"""
Quality rules — Customers (Silver Layer)
=========================================
Each rule is a SQL expression that must evaluate to TRUE for a record
to be considered valid. Used by 02_silver_transformation.py to build
the is_quarantined flag and the AUTO CDC flow.
"""


def get_customer_rules():
    return {
        "valid_customer_id":    "customer_id IS NOT NULL",
        "valid_age":            "age > 0 AND age < 120",
        "valid_contract_type":  "contract_type IN ('monthly', 'annual')",
        "valid_monthly_fee":    "monthly_fee >= 0",
    }


def get_usage_rules():
    return {
        "valid_customer_id":        "customer_id IS NOT NULL",
        "valid_year_month":         "year_month IS NOT NULL",
        "valid_data_consumed":      "data_consumed_gb >= 0",
        "valid_call_minutes":       "call_minutes >= 0",
        "valid_bill_amount":        "bill_amount >= 0",
    }


def get_label_rules():
    return {
        "valid_customer_id":        "customer_id IS NOT NULL",
        "valid_year_month":         "year_month IS NOT NULL",
    }


def get_interaction_rules():
    return {
        "valid_customer_id":        "customer_id IS NOT NULL",
        "valid_timestamp":          "timestamp IS NOT NULL",
        "valid_interaction_type":   (
            "interaction_type IN ("
            "'call_center_inquiry', 'call_center_complaint', 'online_chat',"
            "'store_visit', 'plan_upgrade', 'plan_downgrade', 'plan_renewal',"
            "'technical_support', 'billing_dispute', 'cancellation_request',"
            "'loyalty_offer_accepted', 'loyalty_offer_rejected', 'port_out_request'"
            ")"
        ),
    }
