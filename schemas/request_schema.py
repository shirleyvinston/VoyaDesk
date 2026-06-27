from marshmallow import Schema, fields

class TravelRequestSchema(Schema):

    project_name = fields.Str(required=True)
    site_name = fields.Str(required=True)

    request_date = fields.Str(required=True)
    departure_date = fields.Str(required=True)
    return_date = fields.Str(required=True)

    total_days = fields.Int(required=True)

    period_name = fields.Str(required=True)

    quarter = fields.Str(required=True)

    amount_requested = fields.Float(required=True)

    purpose = fields.Str(required=True)

    reason_text = fields.Str(required=True)