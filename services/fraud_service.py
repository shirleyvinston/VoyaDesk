def analyze_settlement(settlement, expenses):

    total_expense = float(
        settlement['expense_incurred'] or 0
    )

    advance = float(
        settlement['advance_received'] or 0
    )

    fraud_score = 0
    remarks = []

    # =====================================
    # HIGH HOTEL EXPENSE
    # =====================================

    for expense in expenses:

        amount = float(
            expense['amount']
        )

        if (
            expense['expense_type'] == 'Hotel'
            and amount > 5000
        ):
            fraud_score += 20

            remarks.append(
                "Hotel expense unusually high"
            )

        if (
            expense['expense_type'] == 'Food'
            and amount > 1000
        ):
            fraud_score += 15

            remarks.append(
                "Food expense unusually high"
            )

    # =====================================
    # HIGH TOTAL CLAIM
    # =====================================

    if total_expense > 20000:

        fraud_score += 30

        remarks.append(
            "High total settlement amount"
        )

    # =====================================
    # MANY CLAIMS
    # =====================================

    if len(expenses) > 5:

        fraud_score += 20

        remarks.append(
            "Large number of expense claims"
        )

    # =====================================
    # COMPARE AGAINST ADVANCE
    # =====================================

    if (
        advance > 0
        and
        total_expense > advance * 2
    ):

        fraud_score += 40

        remarks.append(
            "Expense exceeds advance significantly"
        )

    # =====================================
    # COMPARE CLAIM VS REQUESTED AMOUNT
    # =====================================

    if (
        advance > 0
        and
        total_expense > advance * 1.5
    ):

        fraud_score += 20

        remarks.append(
            "Claim exceeds requested amount by 50%"
        )

    # =====================================
    # DUPLICATE BILL NUMBERS
    # =====================================

    seen_bills = set()

    for expense in expenses:

        bill_no = expense.get(
            'bill_no'
        )

        if not bill_no:
            continue

        if bill_no in seen_bills:

            fraud_score += 50

            remarks.append(
                "Duplicate bill number detected"
            )

        seen_bills.add(bill_no)

    # =====================================
    # EXCESSIVE DAILY SPENDING
    # =====================================

    try:

        days = (
            settlement['arrival_date']
            -
            settlement['departure_date']
        ).days + 1

        if days > 0:

            daily_average = (
                total_expense / days
            )

            if daily_average > 5000:

                fraud_score += 25

                remarks.append(
                    "Very high daily spending pattern"
                )

    except Exception:

        pass

    # =====================================
    # RISK LEVEL
    # =====================================

    if fraud_score >= 100:

        risk = "HIGH"

        recommendation = (
            "Manual Review Required"
        )

    elif fraud_score >= 50:

        risk = "MEDIUM"

        recommendation = (
            "Review Supporting Documents"
        )

    else:

        risk = "LOW"

        recommendation = (
            "Safe To Approve"
        )

    return {

        "score": fraud_score,

        "risk": risk,

        "recommendation": recommendation,

        "remarks": ", ".join(remarks)

    }