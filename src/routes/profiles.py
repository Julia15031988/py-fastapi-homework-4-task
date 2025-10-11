from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.schemas.profiles import ProfileCreateSchema, ProfileResponseSchema
from src.database.models.accounts import UserModel, UserProfileModel
from src.security.interfaces import JWTAuthManagerInterface
from src.config.dependencies import get_db, get_s3_storage_client, get_jwt_auth_manager
from src.utils.token import get_token
from validation import validate_image

router = APIRouter()


@router.post("/users/{user_id}/profile/", response_model=ProfileResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_user_profile(
    user_id: int,
    request: Request,
    avatar: UploadFile=File(...),
    data: ProfileCreateSchema=Depends(),
    db: AsyncSession=Depends(get_db),
    jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager),
    s3_client = Depends(get_s3_storage_client),
):
    # Token validation
    token = get_token(request)
    try:
        payload = jwt_manager.decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Token has expired.")

    current_user_id = int(payload["sub"])
    current_user_role = payload.get("role", "user")

    if current_user_id != user_id and current_user_role != "admin":
        raise HTTPException(status_code=403, detail="You don't have permission to edit this profile.")

    user = await db.scalar(select(UserModel).where(UserModel.id == user_id, UserModel.is_active))
    if not user:
        raise HTTPException(status_code=401, detail="User not found or not active.")

    existing_profile = await db.scalar(select(UserProfileModel).where(UserProfileModel.user_id == user_id))
    if existing_profile:
        raise HTTPException(status_code=400, detail="User already has a profile.")

    # Validate image separately
    try:
        validate_image(avatar)
    except ValueError as ve:
        raise HTTPException(status_code=422, detail=str(ve))

    # Upload avatar
    try:
        avatar_url = await s3_client.upload_avatar(user_id=user_id, file=avatar)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to upload avatar. Please try again later.")

    profile = UserProfileModel(
        user_id=user_id,
        first_name=data.first_name,
        last_name=data.last_name,
        gender=data.gender,
        date_of_birth=data.date_of_birth,
        info=data.info,
        avatar=avatar_url
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)

    return profile
