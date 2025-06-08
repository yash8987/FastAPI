from fastapi import FastAPI, Depends, HTTPException
from fastapi.openapi.utils import get_openapi
from sqlalchemy.orm import Session
import models, schemas, utils, database, auth
from database import get_db

app = FastAPI()

models.Base.metadata.create_all(bind=database.engine)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="FastAPI Email Sender",
        version="1.0.0",
        description="API to send emails and view logs using JWT authentication",
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }

    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            if "security" not in openapi_schema["paths"][path][method]:
                openapi_schema["paths"][path][method]["security"] = [{"BearerAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

@app.post("/register")
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter_by(username=user.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    
    hashed_pw = auth.get_password_hash(user.password)
    new_user = models.User(username=user.username, hashed_password=hashed_pw)
    db.add(new_user)
    db.commit()
    return {"Success" : True, "message" : "User Registered Successfully"}

@app.post("/login", response_model=schemas.Token)
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter_by(username=user.username).first()
    if not db_user or not auth.verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = auth.create_access_token(data={"sub": db_user.username})
    return {"access_token": token, "token_type": "bearer"}

@app.post("/send-email", response_model=schemas.EmailLogSchema)
def send_email(email: schemas.EmailSchema,
               db: Session = Depends(get_db),
               current_user: models.User = Depends(auth.get_current_user)):

    status = utils.send_email(email.recipient, email.subject, email.body)
    log = models.EmailLog(
        recipient=email.recipient,
        subject=email.subject,
        body=email.body,
        status=status,
        user_id=current_user.id
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

@app.get("/logs", response_model=list[schemas.EmailLogSchema])
def get_logs(db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)):
    allLogs = db.query(models.EmailLog).filter_by(user_id=current_user.id).all()
    return allLogs