"""TypeSafe Jev: typed questions in, calibrated probabilities out (docs.typesafe.ai).

The assistant asks Jev narrow questions about each customer turn (what they want, why they're
returning something, which order line they mean, whether they want a person) in one request,
then code decides what to do with the answers and their confidence. Jev never decides
eligibility, amounts, or confirmation; those come from the commerce API and the app.
"""
