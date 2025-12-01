"""
Authentication API endpoints.

Handles user registration, login, token refresh, and password management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    verify_token,
)
from app.database.models import User
from app.database.session import get_db
from app.dependencies import get_current_user
from app.repositories import UserRepository
from app.schemas import (
    LoginRequest,
    PaperlessCredentialsUpdate,
    TokenRefreshRequest,
    TokenResponse,
    UserCreate,
    UserPasswordChange,
    UserResponse,
    UserUpdate,
)
from app.services.paperless import get_paperless_client


logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Register a new user account.

    Validates Paperless credentials before creating the account.
    """
    user_repo = UserRepository(db)

    # Check if username already exists
    if await user_repo.username_exists(user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )

    # Check if email already exists
    if user_data.email and await user_repo.email_exists(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Validate Paperless credentials
    try:
        paperless_client = await get_paperless_client(
            base_url=user_data.paperless_url,
            auth_token=user_data.paperless_token,
        )
        is_valid = await paperless_client.health_check()

        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Paperless credentials or URL",
            )

        await paperless_client.close()

    except Exception as e:
        logger.error(f"Paperless validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not validate Paperless credentials",
        )

    # Create user
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        role=user_data.role,
        paperless_url=user_data.paperless_url,
        paperless_username=user_data.paperless_username,
        paperless_token=user_data.paperless_token,
    )

    created_user = await user_repo.create(user)
    logger.info(f"User registered: {created_user.username}")

    return created_user


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Login and receive access and refresh tokens.
    """
    user_repo = UserRepository(db)

    # Get user by username
    user = await user_repo.get_by_username(credentials.username)

    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    # Create tokens
    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))

    logger.info(f"User logged in: {user.username}")

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_data: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Refresh access token using refresh token.
    """
    user_id_str = verify_token(token_data.refresh_token, token_type="refresh")

    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify user still exists and is active
    user_repo = UserRepository(db)
    from uuid import UUID
    user = await user_repo.get_by_id(UUID(user_id_str))

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Create new tokens
    access_token = create_access_token(subject=str(user.id))
    new_refresh_token = create_refresh_token(subject=str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current user information.
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Update current user information.

    Allows updating email, timezone, and other user preferences.
    Does not update password (use /auth/password endpoint instead).
    Does not update Paperless credentials (use /auth/paperless-credentials endpoint instead).
    """
    user_repo = UserRepository(db)

    # Update only the fields that are provided
    if user_data.email is not None:
        # Check if email is already in use by another user
        if user_data.email != current_user.email:
            existing_user = await user_repo.get_by_email(user_data.email)
            if existing_user and existing_user.id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already in use",
                )
        current_user.email = user_data.email

    if user_data.timezone is not None:
        current_user.timezone = user_data.timezone

    if user_data.is_active is not None:
        current_user.is_active = user_data.is_active

    # Update user in database
    updated_user = await user_repo.update(current_user)

    logger.info(f"User updated: {current_user.username}")

    return updated_user


@router.put("/password")
async def change_password(
    password_data: UserPasswordChange,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Change user password.
    """
    # Verify current password
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Update password
    current_user.password_hash = hash_password(password_data.new_password)

    user_repo = UserRepository(db)
    await user_repo.update(current_user)

    logger.info(f"Password changed for user: {current_user.username}")

    return {"message": "Password updated successfully"}


@router.put("/paperless-credentials")
async def update_paperless_credentials(
    credentials: PaperlessCredentialsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Update Paperless-ngx credentials for the current user.

    Validates the new credentials before updating them in the database.

    Security: If the username has changed, a new token must be provided.
    If the username is the same, an empty token will use the existing token.
    """
    # Security check: If username changed, require a new token
    username_changed = credentials.paperless_username != current_user.paperless_username
    if username_changed and not credentials.paperless_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authentication token is required when changing the username",
        )

    # Determine which token to use for validation
    token_to_use = credentials.paperless_token if credentials.paperless_token else current_user.paperless_token

    # Validate new Paperless credentials
    try:
        paperless_client = await get_paperless_client(
            base_url=credentials.paperless_url,
            auth_token=token_to_use,
        )
        is_valid = await paperless_client.health_check()

        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Paperless credentials or URL",
            )

        await paperless_client.close()

    except HTTPException:
        # Re-raise HTTP exceptions from validation
        raise
    except Exception as e:
        logger.error(f"Paperless validation failed for user {current_user.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not validate Paperless credentials",
        )

    # Update user's Paperless credentials
    current_user.paperless_url = credentials.paperless_url
    current_user.paperless_username = credentials.paperless_username
    # Only update token if a new one was provided
    if credentials.paperless_token:
        current_user.paperless_token = credentials.paperless_token

    user_repo = UserRepository(db)
    await user_repo.update(current_user)

    logger.info(f"Paperless credentials updated for user: {current_user.username}")

    return {"message": "Paperless credentials updated successfully"}


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Logout (client-side token removal).

    Note: Since we use stateless JWT tokens, actual logout happens client-side.
    This endpoint is provided for consistency and future token blacklisting.
    """
    logger.info(f"User logged out: {current_user.username}")
    return {"message": "Logged out successfully"}
