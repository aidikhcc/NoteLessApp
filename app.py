from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from extensions import db, login_manager, csrf
from models import User, Session, Question, Response, Agent, AgentResponse
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import qrcode
import os
from io import BytesIO
import base64
from agent import get_available_llms, process_session_data
from dotenv import load_dotenv, set_key

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///noteless.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
login_manager.init_app(app)
csrf.init_app(app)

login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        
        flash('Invalid username or password', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', sessions=current_user.sessions)

@app.route('/create_session', methods=['GET', 'POST'])
@login_required
def create_session():
    if request.method == 'POST':
        session_name = request.form.get('name')
        if not session_name:
            flash('Session name is required', 'error')
            return render_template('create_session.html')
            
        access_code = os.urandom(5).hex()
        new_session = Session(name=session_name, admin_id=current_user.id, access_code=access_code)
        db.session.add(new_session)
        db.session.commit()

        # Add default question
        default_question = Question(
            text="What is the project Description?",
            session_id=new_session.id
        )
        db.session.add(default_question)
        db.session.commit()

        return redirect(url_for('session_detail', session_id=new_session.id))
    return render_template('create_session.html')

@app.route('/session/<int:session_id>')
@login_required
def session_detail(session_id):
    session = Session.query.get_or_404(session_id)
    if session.admin_id != current_user.id:
        flash('You do not have permission to view this session', 'error')
        return redirect(url_for('dashboard'))
    
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(f"{request.host_url}join/{session.access_code}")
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert QR code to base64 for embedding in HTML
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    qr_code = base64.b64encode(buffered.getvalue()).decode()
    
    return render_template('session_detail.html', session=session, qr_code=qr_code)

@app.route('/session/<int:session_id>/questions', methods=['POST'])
@login_required
def add_question(session_id):
    session = Session.query.get_or_404(session_id)
    if session.admin_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.json
    question_text = data.get('text')
    if not question_text:
        return jsonify({'error': 'Question text is required'}), 400
    
    new_question = Question(text=question_text, session_id=session_id)
    db.session.add(new_question)
    db.session.commit()
    
    return jsonify({'message': 'Question added successfully'})

@app.route('/question/<int:question_id>/delete', methods=['POST'])
@login_required
def delete_question(question_id):
    question = Question.query.get_or_404(question_id)
    if question.session.admin_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.delete(question)
    db.session.commit()
    return jsonify({'message': 'Question deleted successfully'})

@app.route('/session/<int:session_id>/delete', methods=['POST'])
@login_required
def delete_session(session_id):
    session = Session.query.get_or_404(session_id)
    if session.admin_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.delete(session)
    db.session.commit()
    return jsonify({'message': 'Session deleted successfully'})

@app.route('/join/<access_code>')
def join_session(access_code):
    session = Session.query.filter_by(access_code=access_code).first_or_404()
    return render_template('participant_view.html', session=session)

@app.route('/question/<int:question_id>/responses')
@login_required
def view_responses(question_id):
    question = Question.query.get_or_404(question_id)
    if question.session.admin_id != current_user.id:
        flash('You do not have permission to view these responses', 'error')
        return redirect(url_for('dashboard'))
    return render_template('responses.html', question=question)

@app.route('/question/<int:question_id>/respond', methods=['POST'])
def submit_response(question_id):
    if not request.is_json:
        return jsonify({'error': 'Invalid request'}), 400
    
    data = request.get_json()
    text = data.get('text')
    
    if not text or not text.strip():
        return jsonify({'error': 'Response text is required'}), 400
        
    try:
        # Create new response
        response = Response(
            text=text.strip(),
            question_id=question_id,
            created_at=datetime.utcnow()
        )
        db.session.add(response)
        db.session.commit()
        
        return jsonify({'message': 'Response submitted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error submitting response: {e}")
        return jsonify({'error': 'Failed to submit response'}), 500

@app.route('/settings')
@login_required
def settings():
    # Load current API keys from .env
    load_dotenv()
    openai_key = os.getenv('OPENAI_API_KEY', '')
    deepseek_key = os.getenv('DEEPSEEK_API_KEY', '')
    
    # Mask the API keys for display
    if openai_key:
        openai_key = openai_key[:6] + '*' * (len(openai_key) - 6)
    if deepseek_key:
        deepseek_key = deepseek_key[:6] + '*' * (len(deepseek_key) - 6)
    
    agents = Agent.query.all()
    return render_template('settings.html', agents=agents, openai_key=openai_key, deepseek_key=deepseek_key)

@app.route('/settings/api-keys', methods=['POST'])
@login_required
def update_api_keys():
    openai_key = request.form.get('openai_key')
    deepseek_key = request.form.get('deepseek_key')
    
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    
    if openai_key:
        set_key(env_path, 'OPENAI_API_KEY', openai_key)
        os.environ['OPENAI_API_KEY'] = openai_key  # Update current environment
    if deepseek_key:
        set_key(env_path, 'DEEPSEEK_API_KEY', deepseek_key)
        os.environ['DEEPSEEK_API_KEY'] = deepseek_key  # Update current environment
    
    load_dotenv()  # Reload all environment variables
    flash('API keys updated successfully', 'success')
    return redirect(url_for('settings'))

@app.route('/settings/agents/create', methods=['GET', 'POST'])
@login_required
def create_agent():
    if request.method == 'POST':
        name = request.form.get('name')
        prompt = request.form.get('prompt')
        
        if not name or not prompt:
            flash('Name and prompt are required', 'error')
            return render_template('create_agent.html')
            
        new_agent = Agent(
            name=name,
            prompt=prompt,
            is_custom=True,
            created_by=current_user.id
        )
        db.session.add(new_agent)
        db.session.commit()
        flash('Agent created successfully', 'success')
        return redirect(url_for('settings'))
    return render_template('create_agent.html')

@app.route('/session/<int:session_id>/generate', methods=['GET', 'POST'])
@login_required
def generate_insights(session_id):
    session = Session.query.get_or_404(session_id)
    if session.admin_id != current_user.id:
        flash('You do not have permission to access this session', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST' and (request.is_json or (request.form.get('agent_id') and request.form.get('llm'))):
        try:
            # Get parameters either from JSON or form data
            if request.is_json:
                data = request.get_json()
                agent_id = data.get('agent_id')
                llm_name = data.get('llm')
            else:
                agent_id = request.form.get('agent_id')
                llm_name = request.form.get('llm')
            
            if not agent_id or not llm_name:
                if request.is_json:
                    return jsonify({'error': 'Missing required parameters'}), 400
                else:
                    flash('Please select both an agent and a language model', 'error')
                    return redirect(url_for('generate_insights', session_id=session_id))

            agent = Agent.query.get_or_404(agent_id)
            session_data = process_session_data(session)
            
            from agent import generate_insights as gen_insights
            response_content = gen_insights(agent.prompt, llm_name, session_data)
            
            # Store the agent's response
            agent_response = AgentResponse(
                content=response_content,
                session_id=session_id,
                agent_id=agent_id,
                llm_used=llm_name,
                created_at=datetime.utcnow()
            )
            db.session.add(agent_response)
            db.session.commit()
            
            if request.is_json:
                return jsonify({
                    'content': response_content,
                    'response_id': agent_response.id
                })
            else:
                flash('Insights generated successfully!', 'success')
                return redirect(url_for('generate_insights', session_id=session_id))
        except Exception as e:
            db.session.rollback()
            print(f"Error generating insights: {e}")
            if request.is_json:
                return jsonify({'error': str(e)}), 500
            else:
                flash(f'Error generating insights: {str(e)}', 'error')
                return redirect(url_for('generate_insights', session_id=session_id))

    # GET request or POST without parameters - render the template
    agents = Agent.query.all()
    available_llms = get_available_llms()
    agent_responses = AgentResponse.query.filter_by(session_id=session_id)\
        .order_by(AgentResponse.created_at.desc())\
        .all()
    
    return render_template(
        'generate_insights.html',
        session=session,
        agents=agents,
        available_llms=available_llms,
        agent_responses=agent_responses
    )

@app.route('/settings/agents/<int:agent_id>/modify', methods=['GET', 'POST'])
@login_required
def modify_agent_prompt(agent_id):
    agent = Agent.query.get_or_404(agent_id)
    if not agent.is_custom:
        flash('Cannot modify built-in agent prompts', 'error')
        return redirect(url_for('settings'))
    
    if request.method == 'POST':
        prompt = request.form.get('prompt')
        if not prompt:
            flash('Prompt is required', 'error')
            return render_template('modify_agent.html', agent=agent)
        
        agent.prompt = prompt
        db.session.commit()
        flash('Agent prompt updated successfully', 'success')
        return redirect(url_for('settings'))
    
    return render_template('modify_agent.html', agent=agent)

@app.route('/settings/agents/<int:agent_id>/delete', methods=['POST'])
@login_required
def delete_agent(agent_id):
    agent = Agent.query.get_or_404(agent_id)
    if not agent.is_custom:
        return jsonify({'error': 'Cannot delete built-in agents'}), 403
    
    try:
        db.session.delete(agent)
        db.session.commit()
        return jsonify({'message': 'Agent deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete agent'}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)