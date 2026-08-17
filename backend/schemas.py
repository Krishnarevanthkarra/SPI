from pydantic import BaseModel, EmailStr, Field
from typing import Literal, List, Optional
from datetime import datetime
from .settings import Collections


class Subscription(BaseModel):
    plantype: Literal["trial", "premium", "enterprise"]
    devicesallowed: Literal[1, 5, 10]
    planperiod: Literal[5, 90, 365]
    createdAt: datetime


class Session(BaseModel):
    # sessionid: Optional[str] = Field(default=None, alias='_id')
    userid: str
    devicename: str
    last_used: datetime
    createdAt: datetime


class User(BaseModel):
    # userid: Optional[str] = Field(default=None, alias='_id')
    fullname: str
    password: str
    email: EmailStr
    createdAt: datetime
    subscription: Optional[Subscription] = None


class Organization(BaseModel):
    # userid: Optional[str] = Field(default=None, alias='_id')
    organizationName: str
    password: str
    email: EmailStr
    createdAt: datetime
    subscription: Optional[Subscription] = None


class EmailService(User): ...


class Data(BaseModel):
    cardId: str
    isRootCause: bool


class Measured(BaseModel):
    height: int
    widht: int


class Position(BaseModel):
    x: int
    y: int


class Node(BaseModel):
    data: Data
    measured: Measured
    position: Position
    type: str


class Edge(BaseModel):
    id: str


class Cluster(BaseModel):
    clusterid: str
    nodes: List[Node]
    # edges: List[Edge]


class Token(BaseModel):
    token: str


class TokenBody(BaseModel):
    userid: str
    sessionid: str


class LoginDetails(BaseModel):
    email: EmailStr
    password: str
    devicename: str


class ForgotPasswordInput(BaseModel):
    email: EmailStr
    accType: str = Literal["Organization", "User"]



