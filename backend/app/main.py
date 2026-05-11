from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware

from app.auth import (
    LoginPayload,
    UserCreatePayload,
    UserPasswordPayload,
    UserUpdatePayload,
    attach_session_cookie,
    authenticate_user,
    clear_session_cookie,
    create_user,
    ensure_users_table,
    get_current_user,
    list_users,
    require_admin_user,
    update_user,
    update_user_password,
)
from app.config import settings
from app.dashboard import get_dashboard_payload
from app.database import check_database_connection

app = FastAPI(title="Dashboard API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    ensure_users_table()


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Dashboard API is running"}


@app.get("/health")
def health_check() -> dict[str, object]:
    try:
        database = check_database_connection()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {exc}") from exc

    return {"status": "ok", "database": database}


@app.post("/api/auth/login")
def login(payload: LoginPayload, response: Response) -> dict[str, object]:
    user = authenticate_user(payload.username, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiant ou mot de passe incorrect.",
        )

    attach_session_cookie(response, user)
    return {"user": user}


@app.get("/api/auth/me")
def read_current_user(current_user: dict[str, object] = Depends(get_current_user)) -> dict[str, object]:
    return {"user": current_user}


@app.post("/api/auth/logout")
def logout(response: Response) -> dict[str, str]:
    clear_session_cookie(response)
    return {"status": "ok"}


@app.get("/api/users")
def users(current_user: dict[str, object] = Depends(require_admin_user)) -> dict[str, object]:
    return {"users": list_users()}


@app.post("/api/users", status_code=status.HTTP_201_CREATED)
def add_user(
    payload: UserCreatePayload,
    current_user: dict[str, object] = Depends(require_admin_user),
) -> dict[str, object]:
    try:
        user = create_user(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return {"user": user}


@app.patch("/api/users/{user_id}")
def edit_user(
    user_id: int,
    payload: UserUpdatePayload,
    current_user: dict[str, object] = Depends(require_admin_user),
) -> dict[str, object]:
    try:
        user = update_user(user_id, payload, current_user_id=int(current_user["id"]))
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return {"user": user}


@app.post("/api/users/{user_id}/password", status_code=status.HTTP_204_NO_CONTENT)
def change_user_password(
    user_id: int,
    payload: UserPasswordPayload,
    current_user: dict[str, object] = Depends(require_admin_user),
) -> Response:
    try:
        update_user_password(user_id, payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/api/dashboard")
def dashboard_data(current_user: dict[str, object] = Depends(get_current_user)) -> dict[str, object]:
    try:
        return get_dashboard_payload()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Unable to load dashboard data: {exc}") from exc
