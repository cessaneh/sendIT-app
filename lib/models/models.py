from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship, validates
from sqlalchemy_serializer import SerializerMixin
from .database import db


class User(db.Model, UserMixin, SerializerMixin):
    __tablename__ = "users"
    serialize_rules = (
        "-orders.user",
        "-parcels.user",
        "-password",
    )

    id = Column(Integer, primary_key=True)
    username = Column(String(150), nullable=False, unique=True)
    email = Column(String(150), unique=True, nullable=False)
    hashed_password = Column(String(256), nullable=False)
    role = Column(String(50), nullable=False, default="user")
    orders = relationship("Order", backref="user", lazy=True)
    parcels = relationship("Parcel", backref="user", lazy=True)
    profiles = relationship("Profile", backref="user", lazy=True)

    def __init__(self, email, username, role, hashed_password):
        from app import bcrypt

        self.email = email
        self.username = username
        self.role = role
        self.hashed_password = hashed_password

    @validates("email")
    def validate_email(self, key, email):
        import re

        regex = r"^\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        if not re.match(regex, email):
            raise ValueError("Invalid email address")
        return email

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
        }

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"


class Order(db.Model, SerializerMixin):
    __tablename__ = "orders"
    serialize_rules = (
        "-user.orders",
        "-feedback.order",
    )

    order_id = Column(Integer, primary_key=True)
    pickup_address = Column(Text, nullable=False)
    delivery_address = Column(Text, nullable=False)
    status = Column(String(50), default="pending")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    feedback = relationship("Feedback", backref="order", lazy=True)

    def __repr__(self):
        return (
            f"<Order(order_id={self.order_id}, pickup_address={self.pickup_address})>"
        )


class Parcel(db.Model, SerializerMixin):
    __tablename__ = "parcels"
    serialize_rules = ("-user.parcels",)

    id = Column(Integer, primary_key=True)
    pickup_location = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    weight = Column(Float, nullable=False)
    price = Column(Float, nullable=True)
    description = Column(String)

    def __repr__(self):
        return f"<Parcel(id={self.id}, pickup_location={self.pickup_location}, destination={self.destination})>"


class Profile(db.Model, SerializerMixin):
    __tablename__ = "profiles"
    serialize_rules = ("-user.profiles",)

    id = Column(Integer, primary_key=True)
    profile_picture = Column(String(255))
    location = Column(String)
    created_at = Column(DateTime, default=db.func.now())
    user_id = Column(Integer, ForeignKey("users.id"))

    def __repr__(self):
        return f"<Profile(id={self.id}, location={self.location})>"


class Feedback(db.Model, SerializerMixin):
    __tablename__ = "feedback"
    serialize_rules = ("-order.feedback",)

    id = Column(Integer, primary_key=True)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=False)
    order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=False)

    def __repr__(self):
        return f"<Feedback(id={self.id}, rating={self.rating})>"
