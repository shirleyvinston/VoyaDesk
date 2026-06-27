from openai import OpenAI

client = OpenAI(
    api_key="YOUR_API_KEY"
)

def generate_management_summary(
    total_expense,
    top_employee,
    top_project,
    high_risk_count
):

    prompt = f"""
    You are a travel expense auditor.

    Total spending: ₹{total_expense}

    Highest spending employee:
    {top_employee}

    Highest spending project:
    {top_project}

    High risk settlements:
    {high_risk_count}

    Generate a professional executive summary.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role":"user",
                "content":prompt
            }
        ]
    )

    return response.choices[0].message.content