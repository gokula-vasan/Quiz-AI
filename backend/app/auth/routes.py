from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.database import get_database
from app.models.user import UserRegister, UserResponse, UserInDB
from app.auth.security import get_password_hash, verify_password, create_access_token
from app.auth.dependencies import get_current_user
from datetime import datetime

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserRegister):
    db = get_database()
    
    # Check if email already exists
    existing_user = await db.users.find_one({"email": user_in.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists."
        )
        
    # Check if username exists
    existing_username = await db.users.find_one({"username": user_in.username})
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this username already exists."
        )
    
    hashed_password = get_password_hash(user_in.password)
    user_db = UserInDB(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hashed_password,
        created_at=datetime.utcnow()
    )
    
    user_dict = user_db.model_dump(by_alias=True)
    if user_dict.get("_id") is None:
        user_dict.pop("_id", None)
        
    result = await db.users.insert_one(user_dict)
    user_dict["_id"] = result.inserted_id
    
    return UserResponse.model_validate(user_dict)

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    db = get_database()
    
    # Find user by username or email (allows both for login)
    user = await db.users.find_one({
        "$or": [
            {"email": form_data.username},
            {"username": form_data.username}
        ]
    })
    
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user["email"]})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(user["_id"]),
            "username": user["username"],
            "email": user["email"]
        }
    }

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)
