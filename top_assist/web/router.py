import logging

from fastapi import APIRouter, BackgroundTasks, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from top_assist.auth.sign_in_flow import (
    AlreadySignedIn,
    EmailMismatch,
    SignInCompleted,
    SignInLinkExpired,
    generate_provider_oauth_link,
    process_confluence_oauth_callback,
    start_sign_in_flow,
)
from top_assist.utils.metrics import TEST_METRIC
from top_assist.utils.sentry_notifier import sentry_notify_exception, sentry_notify_issue

router = APIRouter()
templates = Jinja2Templates(directory="top_assist/web/html_templates")


@router.get("/test/metric")
def test_metric(background_tasks: BackgroundTasks) -> dict[str, str]:
    background_tasks.add_task(TEST_METRIC.inc, 1)
    background_tasks.add_task(TEST_METRIC.inc, 1)
    return {"message": "Tasks are being processed in the background"}


@router.get("/")
def home() -> Response:
    return RedirectResponse("/admin", status_code=303)


@router.get("/ping")
def pong() -> dict[str, str]:
    return {"ping": "pong"}


@router.get("/confluence/oauth/redirect/{state}")
def redirect(state: str) -> Response:
    url = generate_provider_oauth_link(state=state)

    return RedirectResponse(url)


@router.get("/confluence/oauth/callback", response_class=HTMLResponse)
def confluence_oauth_callback(
    background_tasks: BackgroundTasks, request: Request, state: str | None = None, code: str | None = None
) -> Response:
    response: Response | None = None
    try:
        if state and code:
            response = _confluence_oauth_callback(background_tasks, request, state, code)
        else:
            sentry_notify_issue("Missing state or code in OAuth callback", extra={"state": state, "code": code})

    except Exception as e:
        sentry_notify_exception(e)
        logging.exception("An error occurred in the OAuth callback.")

    return response or templates.TemplateResponse(
        request=request,
        name="auth_status.html",
        context={
            "message_one": "Something went wrong",
            "message_two": "Please try again, if the error persist please reach out to the administrator.",
        },
    )


def _confluence_oauth_callback(
    background_tasks: BackgroundTasks, request: Request, state: str, code: str
) -> Response | None:
    match process_confluence_oauth_callback(encrypted_state=state, code=code):
        case SignInCompleted() as completed:
            background_tasks.add_task(completed.pending_operation.function, completed.pending_operation.arg)
            return templates.TemplateResponse(
                request=request,
                name="auth_status.html",
                context={
                    "message_one": "You have successfully authenticated.",
                    "message_two": "Top Assist will answer your questions on Slack",
                },
            )

        case AlreadySignedIn():
            return templates.TemplateResponse(
                request=request,
                name="auth_status.html",
                context={
                    "message_one": "You are already authenticated.",
                    "message_two": "Top Assist will answer your questions on Slack",
                },
            )

        case SignInLinkExpired() as expired:
            start_sign_in_flow(expired.context_for_retry)
            return templates.TemplateResponse(
                request=request,
                name="auth_status.html",
                context={
                    "message_one": "Your authentication link has expired.",
                    "message_two": "We have sent you a new one. Please check DMs.",
                },
            )

        case EmailMismatch():
            return templates.TemplateResponse(
                request=request,
                name="auth_status.html",
                context={
                    "message_one": "Email mismatch detected.",
                    "message_two": "Please authenticate with the same email as your Slack account.",
                },
            )

        case unknown:
            extra = {"unknown": unknown, "unknown_type": type(unknown)}
            sentry_notify_issue("Unknown processing result in OAuth callback", extra=extra)
            logging.error("Unknown processing result in OAuth callback", extra=extra)
            return None
