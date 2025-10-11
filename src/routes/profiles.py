from fastapi import APIRouter

router = APIRouter()

from fastapi import APIRouter, Depends, UploadFile, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.schemas.profiles import ProfileCreateSchema, ProfileResponseSchema
from src.database.models.accounts import UserModel, UserProfileModel
from src.security.token_manager import JWTAuthManager
from src.security.interfaces import JWTAuthManagerInterface
from src.storages.interfaces import S3StorageInterface
from src.config.settings import BaseAppSettings
from src.config.dependencies import get_db, get_settings, get_s3_storage_client, get_jwt_auth_manager
from src.utils.token import get_token
from validation import validate_image

router = APIRouter()

@router.post("/users/{user_id}/profile/", response_model=ProfileResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_user_profile(
    user_id: int,
    request: Request,
    data: ProfileCreateSchema = Depends(),
    db: AsyncSession = Depends(get_db),
    settings: BaseAppSettings = Depends(get_settings),
    s3_client: S3StorageInterface = Depends(get_s3_storage_client),
    jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager),
):
    # 1️⃣ Token validation
    token = get_token(request)
    payload = jwt_manager.decode_access_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Token has expired.")

    current_user_id = int(payload["sub"])
    current_user_role = payload.get("role", "user")

    # 2️⃣ Authorization
    if current_user_id != user_id and current_user_role != "admin":
        raise HTTPException(status_code=403, detail="You don't have permission to edit this profile.")

    # 3️⃣ User existence
    user = await db.scalar(select(UserModel).where(UserModel.id == user_id, UserModel.is_active == True))
    if not user:
        raise HTTPException(status_code=401, detail="User not found or not active.")

    # 4️⃣ Existing profile check
    existing_profile = await db.scalar(select(UserProfileModel).where(UserProfileModel.user_id == user_id))
    if existing_profile:
        raise HTTPException(status_code=400, detail="User already has a profile.")

    # 5️⃣ Avatar validation and upload
    try:
        validate_image(data.avatar)
        avatar_path = await s3_client.upload_avatar(user_id=user_id, file=data.avatar)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to upload avatar. Please try again later.")

    # 6️⃣ Create profile
    profile = UserProfileModel(
        user_id=user_id,
        first_name=data.first_name,
        last_name=data.last_name,
        gender=data.gender,
        date_of_birth=data.date_of_birth,
        info=data.info,
        avatar=avatar_path
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)

    return ProfileResponseSchema(
        id=profile.id,
        user_id=profile.user_id,
        first_name=profile.first_name,
        last_name=profile.last_name,
        gender=profile.gender,
        date_of_birth=profile.date_of_birth,
        info=profile.info,
        avatar=profile.avatar
    )
