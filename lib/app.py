from flask import Flask, jsonify, request, session, render_template
from flask_restful import Api, Resource
from flask_migrate import Migrate
from flask_cors import CORS
from werkzeug.exceptions import NotFound
from models.models import User, Order, Parcel, Profile, Feedback
from models.database import db
from flask_bcrypt import Bcrypt
import datetime
import jwt
import os
import hashlib
from dotenv import load_dotenv

load_dotenv()

app = Flask(
    __name__,
    static_url_path="",
    static_folder="../client/build",
    template_folder="../client/build",
)

print(f'{os.getenv("DATABASE_NAME")}')
# Check for DATABASE_URI and SECRET_KEY
if not os.getenv("DATABASE_NAME"):
    raise ValueError("DATABASE_NAME not set in .env file")
if not os.getenv("SECRET_KEY"):
    raise ValueError("SECRET_KEY not set in .env file")

database_path = os.path.join(
    os.path.dirname(__file__), "instance", f"{os.getenv('DATABASE_NAME')}"
)

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{database_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SESSION_TYPE"] = "filesystem"

db.init_app(app)
bcrypt = Bcrypt(app)
migrate = Migrate(app, db)
CORS(app, supports_credentials=True)

api = Api(app)


@app.errorhandler(404)
def not_found(e):
    return render_template("index.html")


@app.errorhandler(NotFound)
def handle_not_found(e):
    return (
        jsonify(
            {"error": "Not Found", "message": "The requested resource does not exist."}
        ),
        404,
    )


class Index(Resource):
    def get(self):
        return {"index": "Welcome to Sendit"}


class UserResource(Resource):
    def post(self):
        if request.is_json:
            if request.path.endswith("/login"):
                return self.login()
            elif request.path.endswith("/logout"):
                return self.logout()
            else:
                return self.register()
        else:
            return {"error": "Invalid JSON format"}, 400

    def register(self):
        data = request.get_json()
        username = data.get("username")
        email = data.get("email")
        password = data.get("password")
        role = data.get("role", "user")  # Default to 'user' if not provided

        if not username or not email or not password:
            return {"error": "Missing fields"}, 400

        if User.query.filter_by(email=email).first():
            return {"error": "Email already exists"}, 400

        hashed_password = hashlib.sha256(password.encode("utf-8")).hexdigest()
        new_user = User(
            username=username, email=email, role=role, hashed_password=hashed_password
        )
        db.session.add(new_user)
        db.session.commit()
        return {"user": new_user.to_dict()}, 201

    def login(self):
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")

        user = User.query.filter_by(email=email).first()
        hashed_password = hashlib.sha256(password.encode("utf-8")).hexdigest()
        if user and user.hashed_password == hashed_password:
            session["user_id"] = user.id
            token = jwt.encode(
                {
                    "identity": user.id,
                    "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),
                },
                app.config["SECRET_KEY"],
                algorithm="HS256",
            )

            refresh_token = jwt.encode(
                {
                    "identity": user.id,
                    "exp": datetime.datetime.utcnow() + datetime.timedelta(days=30),
                },
                app.config["SECRET_KEY"],
                algorithm="HS256",
            )

            return {"token": token, "refresh_token": refresh_token}, 200

        return {"error": "Invalid credentials"}, 401

    def logout(self):
        session.pop("user_id", None)
        return {"message": "Logged out successfully"}, 200


class OrderResource(Resource):
    def post(self):
        data = request.get_json()
        new_order = Order(
            user_id=data["user_id"],
            parcel_id=data["parcel_id"],
            origin=data["origin"],
            destination=data["destination"],
            status=data.get("status", "pending"),
        )
        db.session.add(new_order)
        db.session.commit()
        return {"message": "Order created", "order": new_order.to_dict()}, 201

    def get(self, order_id=None):
        if order_id:
            order = Order.query.get(order_id)
            if order:
                return {"order": order.to_dict()}
            return {"error": "Order not found"}, 404

        orders = Order.query.all()
        return {"orders": [order.to_dict() for order in orders]}

    def patch(self, order_id):
        order = Order.query.get(order_id)
        if not order:
            return {"error": "Order not found"}, 404
        data = request.get_json()
        if "status" in data:
            order.status = data["status"]
        db.session.commit()
        return {"message": "Order updated", "order": order.to_dict()}, 200

    def delete(self, order_id):
        order = Order.query.get(order_id)
        if not order:
            return {"error": "Order not found"}, 404
        db.session.delete(order)
        db.session.commit()
        return {"message": "Order successfully deleted"}, 200


class ParcelResource(Resource):
    def post(self):
        data = request.get_json()
        new_parcel = Parcel(
            weight=data["weight"],
            dimensions=data["dimensions"],
            description=data["description"],
        )
        db.session.add(new_parcel)
        db.session.commit()
        return {"message": "Parcel created", "parcel": new_parcel.to_dict()}, 201

    def get(self):
        parcels = Parcel.query.all()
        return {"parcels": [parcel.to_dict() for parcel in parcels]}

    def patch(self, parcel_id):
        parcel = Parcel.query.get(parcel_id)
        if not parcel:
            return {"error": "Parcel not found"}, 404
        data = request.get_json()
        if "weight" in data:
            parcel.weight = data["weight"]
        if "dimensions" in data:
            parcel.dimensions = data["dimensions"]
        if "description" in data:
            parcel.description = data["description"]
        db.session.commit()
        return {"message": "Parcel updated", "parcel": parcel.to_dict()}, 200

    def delete(self, parcel_id):
        parcel = Parcel.query.get(parcel_id)
        if not parcel:
            return {"error": "Parcel not found"}, 404
        db.session.delete(parcel)
        db.session.commit()
        return {"message": "Parcel successfully deleted"}, 200


class ProfileResource(Resource):
    def get(self, profile_id):
        profile = Profile.query.get(profile_id)
        if profile:
            return {"profile": profile.to_dict()}
        return {"error": "Profile not found"}, 404

    def patch(self, profile_id):
        profile = Profile.query.get(profile_id)
        if not profile:
            return {"error": "Profile not found"}, 404
        data = request.get_json()
        if "address" in data:
            profile.address = data["address"]
        if "phone_number" in data:
            profile.phone_number = data["phone_number"]
        db.session.commit()
        return {"message": "Profile updated", "profile": profile.to_dict()}, 200


class FeedbackResource(Resource):
    def post(self):
        data = request.get_json()
        new_feedback = Feedback(
            user_id=data["user_id"],
            order_id=data["order_id"],
            feedback=data["feedback"],
        )
        db.session.add(new_feedback)
        db.session.commit()
        return {
            "message": "Feedback submitted",
            "feedback": new_feedback.to_dict(),
        }, 201

    def get(self):
        feedbacks = Feedback.query.all()
        return {"feedbacks": [feedback.to_dict() for feedback in feedbacks]}


api.add_resource(Index, "/")
api.add_resource(
    UserResource,
    "/users",
    "/users/login",
    "/users/signup",
    "/users/logout",
    "/users/<int:user_id>",
)
api.add_resource(OrderResource, "/orders", "/orders/<int:order_id>")
api.add_resource(ParcelResource, "/parcels", "/parcels/<int:parcel_id>")
api.add_resource(ProfileResource, "/profiles/<int:profile_id>")
api.add_resource(FeedbackResource, "/feedbacks", "/feedbacks/<int:feedback_id>")

if __name__ == "__main__":
    app.run(port=5000, debug=True)
