from app import app, db
from models import User, Order, Parcel, Profile, Feedback

with app.app_context():
    # Deleting all records from tables
    db.session.query(Feedback).delete()
    db.session.query(Parcel).delete()
    db.session.query(Order).delete()
    db.session.query(Profile).delete()
    db.session.query(User).delete()

    # Commit the changes
    db.session.commit()
    print("All data deleted!")
