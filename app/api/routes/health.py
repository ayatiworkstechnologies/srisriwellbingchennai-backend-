from fastapi import APIRouter, HTTPException, Query
from pydantic import EmailStr

from ...schemas import HealthResponse
from ...services.mail import send_email

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Health"], summary="Health check")
def healthcheck():
    return HealthResponse(status="ok")


@router.post("/test-mail", tags=["Health"], summary="Test mail functionality")
def test_mail(email: EmailStr = Query(..., description="Email address to send the test email to")):
    try:
        send_email(
            to_email=[email],
            subject="Test Mail API - Sri Sri Wellbeing",
            html_body="<p>This is a test email sent from the FastAPI test-mail endpoint to verify SMTP configuration.</p>",
            text_body="This is a test email sent from the FastAPI test-mail endpoint to verify SMTP configuration.",
        )
        return {"status": "success", "message": f"Test email successfully sent to {email}"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")
