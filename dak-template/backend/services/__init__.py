"""Service layer — pure data-access / business logic, no HTTP.

Routers in api/ call into these functions, which keeps the routers (and
app.py) thin and makes the logic unit-testable without a request.
"""
