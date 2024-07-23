from flask_bcrypt import Bcrypt
from faker import Faker
from app import app
from models.database import db
from models.models import User, Order, Parcel, Profile, Feedback
from sqlalchemy.sql import text
import hashlib

fake = Faker()
bcrypt = Bcrypt(app)


def seed_data():
    with app.app_context():

        with db.engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS feedback;"))
            conn.execute(text("DROP TABLE IF EXISTS parcels;"))
            conn.execute(text("DROP TABLE IF EXISTS orders;"))
            conn.execute(text("DROP TABLE IF EXISTS profiles;"))
            conn.execute(text("DROP TABLE IF EXISTS users;"))

        db.create_all()

        print("Dropped and recreated tables.")

        users = []
        for _ in range(5):
            password = fake.password(length=12)
            hashed_password = hashlib.sha256(password.encode("utf-8")).hexdigest()
            user = User(
                username=fake.user_name(),
                email=fake.unique.email(),
                hashed_password=hashed_password,
                role=fake.random_element(elements=("admin", "customer")),
            )
            users.append(user)
            print(
                f"Added user: {user.username}, email: {user.email}, password: {password}"
            )
        db.session.add_all(users)
        db.session.commit()

        print("Seeded Users.")

        orders = []
        for _ in range(5):
            order = Order(
                pickup_address=fake.address(),
                delivery_address=fake.address(),
                status=fake.random_element(
                    elements=("pending", "shipped", "delivered", "canceled")
                ),
                user_id=fake.random_element(elements=[user.id for user in users]),
            )
            orders.append(order)
            print(f"Added order with status: {order.status}")
        db.session.add_all(orders)
        db.session.commit()

        print("Seeded Orders.")

        parcels = []
        for _ in range(10):
            parcel = Parcel(
                pickup_location=fake.address(),
                destination=fake.address(),
                user_id=fake.random_element(elements=[user.id for user in users]),
                weight=fake.random_number(digits=2),
                price=fake.random_number(digits=3),
                description=fake.text(max_nb_chars=200),
            )
            parcels.append(parcel)
            print(f"Added parcel from {parcel.pickup_location} to {parcel.destination}")
        db.session.add_all(parcels)
        db.session.commit()

        print("Seeded Parcels.")

        profiles = []
        for user in users:
            profile = Profile(
                profile_picture=fake.image_url(), location=fake.city(), user_id=user.id
            )
            profiles.append(profile)
            print(f"Added profile for user {user.username} in {profile.location}")
        db.session.add_all(profiles)
        db.session.commit()

        print("Seeded Profiles.")

        feedbacks = []
        for _ in range(5):
            feedback = Feedback(
                rating=fake.random_int(min=1, max=5),
                comment=fake.text(max_nb_chars=200),
                order_id=fake.random_element(
                    elements=[order.order_id for order in orders]
                ),
            )
            feedbacks.append(feedback)
            print(f"Added feedback with rating: {feedback.rating}")
        db.session.add_all(feedbacks)
        db.session.commit()

        print("Seeded Feedbacks.")


if __name__ == "__main__":
    seed_data()
    print("Seeding complete!")
