def generate_ai_insights(
    settlements,
    fraud_data,
    monthly_data
):

    insights = []
    growth=0
    total_expense = 0

    employee_totals = {}
    site_totals = {}
    project_totals = {}
    high_risk_count = 0
    medium_risk_count = 0
    low_risk_count = 0
    for row in settlements:

        amount = float(
            row['expense_incurred'] or 0
        )

        total_expense += amount

        employee = row['emp_name']

        employee_totals[employee] = (
            employee_totals.get(employee, 0)
            + amount
        )

        site = row['place_of_visit']

        site_totals[site] = (
            site_totals.get(site, 0)
            + amount
        )
        project = row['project_code']
        project_totals[project] = (
            project_totals.get(project, 0)
            + amount
        )
    for row in fraud_data:
        if row['risk_level'] == 'HIGH':
            high_risk_count += 1
        elif row['risk_level'] == 'MEDIUM':
            medium_risk_count += 1
        else:
            low_risk_count += 1
    if employee_totals:

        top_employee = max(
            employee_totals,
            key=employee_totals.get
        )

        insights.append(
            f"{top_employee} generated the highest travel expenses."
        )

    if site_totals:

        top_site = max(
            site_totals,
            key=site_totals.get
        )

        insights.append(
            f"Most travel spending occurred in {top_site}."
        )
    if project_totals:
        top_project = max(
        project_totals,
        key=project_totals.get
    )

    insights.append(
        f"{top_project} is the highest spending project."
    )
    if settlements:

        avg = (
            total_expense
            /
            len(settlements)
        )

        insights.append(
            f"Average settlement amount is ₹{avg:,.0f}."
        )

    insights.append(
        f"Total travel spending is ₹{total_expense:,.0f}."
    )

    insights.append(
        f"{high_risk_count} high-risk settlements detected."
    )
    if len(monthly_data) >= 2:
        current_month = float(
        monthly_data[0]['total'] or 0
        )
        previous_month = float(
            monthly_data[1]['total'] or 0
        )
        if previous_month > 0:
            growth = (
            (
                current_month
                -
                previous_month
            )
            /
            previous_month
        ) * 100

            insights.append(
            f"Travel spending changed by {growth:.1f}% compared to last month."
        )
    insights.append(
    f"{high_risk_count} high-risk settlements detected."
)

    insights.append(
    f"{medium_risk_count} medium-risk settlements detected."
)

    insights.append(
    f"{low_risk_count} low-risk settlements detected."
)
    summary = (
    f"Management Summary: "
    f"Total travel spending reached ₹{total_expense:,.0f}. "
    f"The highest spending employee was {top_employee}. "
    f"The most expensive project was {top_project}. "
    f"There are {high_risk_count} high-risk settlements requiring review."
)

    insights.append(summary)
    return {

    "total_expense": total_expense,

    "top_employee": top_employee,

    "top_project": top_project,

    "top_site": top_site,

    "high_risk_count": high_risk_count,

    "medium_risk_count": medium_risk_count,

    "low_risk_count": low_risk_count,

    "growth": growth,

    "summary": summary
}