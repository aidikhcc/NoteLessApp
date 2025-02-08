from app import app, db, User
from werkzeug.security import generate_password_hash
from models import Agent
from prompts import project_manager_prompt

with app.app_context():
    # Drop existing tables and create new ones
    db.drop_all()
    db.create_all()
    
    # Create admin account
    admin = User(
        username="aidiadmin",
        password=generate_password_hash("Khcc@12345")  # Now properly hashing the password
    )
    db.session.add(admin)
    
    # Create default agents
    default_agents = [
        {
            "name": "Project Manager",
            "prompt": project_manager_prompt,
            "is_custom": False
        },
    ]

    for agent_data in default_agents:
        agent = Agent(**agent_data)
        db.session.add(agent)

    db.session.commit()
    print("Database initialized with admin user and default agents")