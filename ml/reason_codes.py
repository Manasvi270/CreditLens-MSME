"""
Standardized Reason Codes Registry for CreditLens-MSME.
Maps model features and contribution directions to standardized reason codes and messages.
"""

REASON_CODES = {
    "debt_to_turnover": {
        "risk_increasing": {
            "code": "RC01",
            "technical_message": "High debt relative to annual turnover is associated with higher predicted risk.",
            "borrower_message": "Your existing debt is high compared to your business turnover."
        },
        "risk_reducing": {
            "code": "RC07",
            "technical_message": "Low debt relative to annual turnover is associated with lower predicted risk.",
            "borrower_message": "Your low existing debt level strengthens your business risk profile."
        }
    },
    "cf_volatility": {
        "risk_increasing": {
            "code": "RC02",
            "technical_message": "High cash flow volatility is associated with higher predicted risk.",
            "borrower_message": "Fluctuations in your monthly cash flow create uncertainty in repayment capacity."
        },
        "risk_reducing": {
            "code": "RC08",
            "technical_message": "Consistent and stable net cash flow is associated with lower predicted risk.",
            "borrower_message": "Consistent monthly cash flow demonstrates steady operating capacity."
        }
    },
    "utility_payment_timeliness": {
        "risk_increasing": {
            "code": "RC03",
            "technical_message": "Delays in utility bill payments are associated with higher predicted risk.",
            "borrower_message": "Occasional delays in utility bill payments negatively impact your score."
        },
        "risk_reducing": {
            "code": "RC06",
            "technical_message": "Timely utility bill payment history is associated with lower predicted risk.",
            "borrower_message": "Prompt utility bill payments demonstrate strong financial discipline."
        }
    },
    "business_vintage_years": {
        "risk_increasing": {
            "code": "RC04",
            "technical_message": "Shorter business vintage is associated with higher predicted risk.",
            "borrower_message": "Your enterprise has a relatively short operating history."
        },
        "risk_reducing": {
            "code": "RC09",
            "technical_message": "Longer business vintage is associated with lower predicted risk.",
            "borrower_message": "Your multi-year operating history builds confidence in business resilience."
        }
    },
    "gst_regularity": {
        "risk_increasing": {
            "code": "RC05",
            "technical_message": "Irregular GST filing history is associated with higher predicted risk.",
            "borrower_message": "Gaps or delays in GST filing regularities add to risk evaluation."
        },
        "risk_reducing": {
            "code": "RC10",
            "technical_message": "Regular and on-time GST filing history is associated with lower predicted risk.",
            "borrower_message": "High GST compliance regularity strongly supports your credit assessment."
        }
    },
    "thin_file_status": {
        "risk_increasing": {
            "code": "RC11",
            "technical_message": "Limited credit bureau history (thin-file) is associated with higher uncertainty.",
            "borrower_message": "Limited bureau history means alternative metrics carry greater weight."
        },
        "risk_reducing": {
            "code": "RC12",
            "technical_message": "Established credit bureau record is associated with lower risk uncertainty.",
            "borrower_message": "An established bureau footprint provides solid credit history baseline."
        }
    },
    "loan_to_turnover": {
        "risk_increasing": {
            "code": "RC13",
            "technical_message": "Large requested loan amount relative to turnover is associated with higher risk.",
            "borrower_message": "The requested loan amount is large relative to your annual revenue."
        },
        "risk_reducing": {
            "code": "RC14",
            "technical_message": "Moderate loan request relative to annual revenue is associated with lower risk.",
            "borrower_message": "Your requested loan size is well-proportioned to your business revenue."
        }
    },
    "digital_payment_share": {
        "risk_increasing": {
            "code": "RC15",
            "technical_message": "Low digital payment footprint is associated with higher prediction variance.",
            "borrower_message": "A lower share of digital transactions reduces alternative payment visibility."
        },
        "risk_reducing": {
            "code": "RC16",
            "technical_message": "High digital transaction share is associated with verifiable revenue streams.",
            "borrower_message": "Strong digital payment adoption provides transparent revenue verification."
        }
    }
}

DEFAULT_REASON_CODE = {
    "risk_increasing": {
        "code": "RC99",
        "technical_message": "Feature contribution is associated with higher predicted risk.",
        "borrower_message": "This metric currently increases your risk evaluation."
    },
    "risk_reducing": {
        "code": "RC98",
        "technical_message": "Feature contribution is associated with lower predicted risk.",
        "borrower_message": "This metric currently supports your risk evaluation."
    }
}

def get_reason_code_info(feature_name: str, direction: str) -> dict:
    """
    Returns reason code metadata (code, technical_message, borrower_message) for a feature.
    """
    feat_entry = REASON_CODES.get(feature_name, {})
    dir_entry = feat_entry.get(direction, DEFAULT_REASON_CODE.get(direction))
    return dir_entry
