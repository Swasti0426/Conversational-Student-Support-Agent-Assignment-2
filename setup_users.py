
from auth_db import create_user

# Create demo student accounts for testing.
demo_users = [
    {
        "username": "student1",
        "password": "Student@123",
        "role": "student",
        "student_id": "STU1001"
    },
    {
        "username": "student2",
        "password": "Student@456",
        "role": "student",
        "student_id": "STU1002"
    }
]

for user in demo_users:
    success, message = create_user(
        username=user["username"],
        password=user["password"],
        role=user["role"],
        student_id=user["student_id"]
    )

    print(f"{user['username']}: {message}")
