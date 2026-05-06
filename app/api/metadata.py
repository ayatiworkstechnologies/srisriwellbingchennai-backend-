API_DESCRIPTION = """
Backend platform for Sri Sri Wellbeing Chennai.

This API serves:
- public content for the website
- public booking and cancellation flows
- contact and lead capture
- admin authentication
- admin content management
- admin booking operations
""".strip()


OPENAPI_TAGS = [
    {
        "name": "Health",
        "description": "Basic uptime and readiness checks for the backend service.",
    },
    {
        "name": "Public Contact",
        "description": "Public enquiry and lead-capture endpoints used by website forms.",
    },
    {
        "name": "Public Content",
        "description": "Website-facing content APIs for services, therapies, camps, and treatments.",
    },
    {
        "name": "Public Booking",
        "description": "Therapy availability, booking creation, and cancellation flows.",
    },
    {
        "name": "Admin Auth",
        "description": "Authentication endpoints for the admin panel.",
    },
    {
        "name": "Admin Dashboard",
        "description": "Dashboard and bootstrap endpoints for loading admin operational data.",
    },
    {
        "name": "Admin CRM",
        "description": "Lead and inquiry management endpoints for admin workflows.",
    },
    {
        "name": "Admin Content",
        "description": "Admin CRUD endpoints for public-facing content entities.",
    },
    {
        "name": "Admin Booking",
        "description": "Admin booking, therapist, and operational scheduling endpoints.",
    },
]
