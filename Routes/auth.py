from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from Database.database import SessionLocal, get_db
from Models.user import User
from Schemas.user import UserCreate, UserOut, UserLogin, Token
from Auth.auth_utils import hash_password, verify_password
from Auth.jwt import create_access_token
from Utils.email_sender import send_confirmation_email
from Auth.dependencies import get_current_user
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter()

@router.post("/register", response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = hash_password(user.password)
    new_user = User(
        name=user.name,
        email=user.email,
        hashed_password=hashed_pw
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    subject = "Welcome to MyShop!"
    body = f"Hello {user.name},\n\nThank you for registering at MyShop.\n\nBest Regards,\nTeam Vasist General Store"
    mail_res = send_confirmation_email(user.email,subject,body)
    if not mail_res:
        raise HTTPException(status_code=500, detail="Registration Successfull, but failed to send confirmation email.")
    return new_user

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == form_data.username).first()
    if not db_user or not verify_password(form_data.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": str(db_user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user

