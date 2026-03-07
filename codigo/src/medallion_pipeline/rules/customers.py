def get_customer_rules():
    return {
        "valid_customer_id": "customer_id IS NOT NULL",
        "valid_age": "age > 0 AND age < 120",
        "valid_contract_type": "contract_type IN ('monthly', 'annual')",
        "valid_monthly_fee": "monthly_fee >= 0",
    }