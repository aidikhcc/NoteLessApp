# Noteless

Noteless is a Flask-based web application designed to help teams manage sessions with sticky-note style questions and responses. It also integrates with multiple language models (LLMs) to generate AI-driven insights based on session data.

## Features

- **User Authentication:** Secure login/logout powered by Flask-Login.
- **Session Management:** Create sessions with unique access codes and QR codes for participants to join.
- **Question & Response Handling:** Add, view, and delete session questions and collect real-time responses.
- **AI Insights Generation:** Leverage various LLMs (e.g., GPT-o3-mini, GPT-o1, Deepseek-R1, Azure-GPT-4o-mini) to automatically generate insights from session data.
- **Agent Management:** Create, modify, and remove custom AI agents. Built-in agents, such as the "Project Manager" agent, help streamline insight generation.
- **API Key Configuration:** Update and manage API keys (for OpenAI, Deepseek, and Azure) via the in-app settings page.

## Installation

### Prerequisites

- Python 3.7 or higher
- pip

### Setup Instructions

1. **Clone the Repository**

   ```bash
   git clone https://your.repo.url/Noteless.git
   cd Noteless
   ```

2. **Create a Virtual Environment and Install Dependencies**

   ```bash
   python -m venv venv
   source venv/bin/activate      # On Windows use: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**

   Create a `.env` file in the project root directory to store your API keys. For example:

   ````env
   OPENAI_API_KEY=your_openai_api_key
   DEEPSEEK_API_KEY=your_deepseek_api_key
   AZURE_OPENAI_API_KEY=your_azure_api_key
   ````

4. **Initialize the Database**

   Run the initialization script to drop existing tables, create new ones, and add the default admin user along with built-in agents:

   ```bash
   python init_db.py
   ```

5. **Run the Application**

   Start the Flask development server:

   ```bash
   python app.py
   ```

   Open your browser and navigate to [http://localhost:5000](http://localhost:5000) to access the application.

## Code Structure

- **app.py:** Main Flask application defining routes and business logic.
- **models.py:** SQLAlchemy models for Users, Sessions, Questions, Responses, Agents, and AgentResponses.
- **agent.py:** Handles integration with language model APIs and insight generation.
- **extensions.py:** Initializes Flask extensions such as SQLAlchemy, CSRF protection, and Flask-Login.
- **init_db.py:** Script used to initialize the database and seed default data.
- **prompts.py:** Contains default agent prompts (e.g., `project_manager_prompt`).

## Usage

- **Admin Dashboard:** Log in as an admin (the default credentials are set during initialization) and access your dashboard to manage sessions.
- **Session Creation:** Create a new session. A unique access code and corresponding QR code are generated for participant use.
- **Collect Responses:** Participants can join a session via the shared QR code or link and submit their responses.
- **Generate Insights:** Use the insights generation page to process session data with an AI agent and review the generated insights.
- **Manage Agents:** From the settings, you can create custom agents or modify existing agent prompts.