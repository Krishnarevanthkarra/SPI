from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pymongo.asynchronous.database import AsyncDatabase
from .. import schemas
from pydantic import EmailStr
from datetime import datetime, timezone
from ..database import get_db
from ..utility.hash_utilities import hash_password, verify_password
from ..utility.email_service import send_email
from urllib.parse import unquote
from ..settings import Collections
from pydantic import EmailStr
from ..utility.session_manage import manageSessions
from ..utility.token_utilities import (
    verify_access_token,
    create_access_token,
    get_current_user,
    oauth2_scheme,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_trail_subscription() -> schemas.Subscription:
    return schemas.Subscription(
        plantype="trial",
        devicesallowed=1,
        planperiod=5,
        createdAt=datetime.now(timezone.utc),
    )


@router.post("/signup/individual", status_code=status.HTTP_200_OK)
async def signup_individual(user: schemas.User, db: AsyncDatabase = Depends(get_db)):
    user_collection = db.get_collection(Collections.USER)
    existing_emails = await user_collection.find_one({"email": user.email})
    if existing_emails:
        raise HTTPException(status_code=409, detail="Email Already Exists.")
    email_collection = db.get_collection(Collections.EMAIL_SERVICE)
    existing_emails = await email_collection.find_one({"email": user.email})
    if existing_emails:
        await email_collection.delete_one({"email": user.email})
    user.password = hash_password(user.password)
    user = user.dict()
    user["subscription"] = get_trail_subscription().dict()
    # del user["userid"]
    await email_collection.insert_one(user)
    await send_email(
        user["email"],
        "Your Balance Cards Verification",
        f"Verfiy You mail by accessing this link.\n\n"
        f"http://localhost:5173/verify/{user["email"]}",
    )
    return {"data": "Activation mail is sent."}


@router.post("/signup/organization", status_code=status.HTTP_200_OK)
async def signup_organization(
    org: schemas.Organization, db: AsyncDatabase = Depends(get_db)
):
    org_collection = db.get_collection(Collections.ORGANIZATION)
    existing_emails = await org_collection.find_one({"email": org.email})
    if existing_emails:
        raise HTTPException(status_code=409, detail="Email Already Exists.")
    email_collection = db.get_collection(Collections.EMAIL_SERVICE)
    existing_emails = await email_collection.find_one({"email": org.email})
    if existing_emails:
        await email_collection.delete_one({"email": org.email})
    org.password = hash_password(org.password)
    org = org.dict()
    org["subscription"] = get_trail_subscription().dict()
    # del org["userid"]
    await email_collection.insert_one(org)
    await send_email(
        org["email"],
        "Your Balance Cards Verification",
        f"Verfiy You mail by accessing this link.\n\n"
        f"http://localhost:5173/verify/{org["email"]}",
    )
    return {"data": "Activation mail is sent."}


@router.post("/verify_email/{email}")
async def verify_user(email: EmailStr, db: AsyncDatabase = Depends(get_db)):
    email_collection = db.get_collection(Collections.EMAIL_SERVICE)
    existing_emails = await email_collection.find_one({"email": email})
    if existing_emails:
        collection_name = ""
        if "fullname" in existing_emails:
            collection_name = Collections.USER
        else:
            collection_name = Collections.ORGANIZATION
        await db.get_collection(collection_name).insert_one(existing_emails)
        await email_collection.delete_one(existing_emails)
        return {"data": "You Account is Activated, Thank You!"}
    if await db.get_collection(Collections.USER).find_one(
        {"email": email}
    ) or await db.get_collection(Collections.ORGANIZATION).find_one({"email": email}):
        return {"data": "Email Already verified Please Kindly Login."}
    raise HTTPException(
        status_code=404, detail="Please kindly SignUp to verify the Account."
    )


@router.post("/login/individual")
async def login_individual(
    credentials=Depends(OAuth2PasswordRequestForm), db: AsyncDatabase = Depends(get_db)
):
    user_collection = db.get_collection(Collections.USER)
    existing_emails = await user_collection.find_one({"email": credentials.username})
    if not existing_emails:
        raise HTTPException(
            status_code=404, detail="Email Id not Found, Please Register Before LogIn."
        )
    if verify_password(credentials.password, existing_emails.get("password")):
        sessionId = await manageSessions(
            credentials.username, credentials.client_id, Collections.USER, db
        )
        userId = str(existing_emails.get("_id"))
        token = create_access_token({"userid": userId, "sessionid": sessionId})
        return {"Token": token}
    raise HTTPException(status_code=401, detail="Invalid Credentails")


@router.post("/login/organization")
async def login_individual(
    credentials=Depends(OAuth2PasswordRequestForm), db: AsyncDatabase = Depends(get_db)
):
    user_collection = db.get_collection(Collections.ORGANIZATION)
    existing_emails = await user_collection.find_one({"email": credentials.username})
    if not existing_emails:
        raise HTTPException(
            status_code=404, detail="Email Id not Found, Please Register Before LogIn."
        )
    if verify_password(credentials.password, existing_emails.get("password")):
        sessionId = await manageSessions(
            credentials.username, credentials.client_id, Collections.ORGANIZATION, db
        )
        userId = str(existing_emails.get("_id"))
        token = create_access_token({"userid": userId, "sessionid": sessionId})
        return {"Token": token}
    raise HTTPException(status_code=401, detail="Invalid Credentails")


@router.post("/forgot_password")
async def forgot_password(
    data: schemas.ForgotPasswordInput, db: AsyncDatabase = Depends(get_db)
):
    collection = db.get_collection(data.accType)
    existing = await collection.find_one({"email": data.email})
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Email Does Not Exist."
        )
    collection = db.get_collection(Collections.FORGOT_PASSWORD)
    existing = await collection.find_one({"email": data.email})
    if not existing:
        await collection.insert_one({"email": data.email, "accountType": data.accType})
        await send_email(
            data.email,
            "Your Change Password Request.",
            f"Change Your password by accessing this link.\n\n"
            + f"http://localhost:5173/change_password/{data.email}",
        )
    return {"data": "Email Sent to the Registered mail Id."}


@router.post("/change_password/{email}")
async def change_password(
    email: EmailStr, password: str, db: AsyncDatabase = Depends(get_db)
):
    collection = db.get_collection(Collections.FORGOT_PASSWORD)
    existing = await collection.find_one({"email": email})
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Please Register for the Forgot Password.",
        )
    acc_collection = db.get_collection(existing.get("accountType"))
    await collection.delete_one({"email": email})

    await acc_collection.update_one(
        {"email": email}, {"$set": {"password": hash_password(password)}}
    )
    return {"data": "Password Change is Successfully done."}


@router.post("/verify_jwt")
async def verify_jwt(
    user=Depends(get_current_user), db: AsyncDatabase = Depends(get_db)
):
    return {"data": user.get("userid")}
