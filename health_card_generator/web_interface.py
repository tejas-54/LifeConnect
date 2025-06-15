from flask import Flask, render_template, request, jsonify, send_file, redirect
import os
import json
from health_card_generator import HealthCardGenerator

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'output'

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Initialize health card generator
generator = HealthCardGenerator(output_dir=app.config['OUTPUT_FOLDER'])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate-donor-card', methods=['GET', 'POST'])
def generate_donor_card():
    if request.method == 'POST':
        # Get form data
        donor_info = {
            "patientId": request.form.get('patientId', f"DONOR_{int(request.form.get('age', '30'))}"),
            "name": request.form.get('name', 'Unknown Donor'),
            "age": int(request.form.get('age', 30)),
            "gender": request.form.get('gender', 'Unknown'),
            "bloodType": request.form.get('bloodType', 'Unknown'),
            "donorStatus": True,
            "recipientStatus": False,
            "organTypes": request.form.getlist('organTypes'),
            "donorConsent": request.form.get('donorConsent') == 'on',
            "familyConsent": request.form.get('familyConsent') == 'on',
            "medicalHistory": {
                "allergies": request.form.get('allergies', '').split(','),
                "medications": request.form.get('medications', '').split(','),
                "surgeries": request.form.get('surgeries', '').split(','),
                "chronicConditions": request.form.get('chronicConditions', '').split(',')
            },
            "organData": {
                "availableOrgans": request.form.getlist('organTypes'),
                "organHealth": {}
            },
            "hospitalId": request.form.get('hospitalId', 'HOSPITAL_001'),
            "hospitalName": request.form.get('hospitalName', 'Unknown Hospital'),
            "doctorName": request.form.get('doctorName', 'Unknown Doctor')
        }
        
        # Generate health card
        result = generator.complete_health_card_workflow(donor_info)
        
        # Return result page
        return render_template('result.html', 
                             card_type="Donor",
                             health_card=result['health_card'],
                             json_path=os.path.basename(result['json_path']),
                             pdf_path=os.path.basename(result['pdf_path']) if result['pdf_path'] else None,
                             image_path=os.path.basename(result['image_path']) if result['image_path'] else None,
                             ipfs_result=result['ipfs_result'])
    
    # GET request - show form
    return render_template('donor_form.html')

@app.route('/generate-recipient-card', methods=['GET', 'POST'])
def generate_recipient_card():
    if request.method == 'POST':
        # Get form data
        recipient_info = {
            "patientId": request.form.get('patientId', f"RECIPIENT_{int(request.form.get('age', '30'))}"),
            "name": request.form.get('name', 'Unknown Recipient'),
            "age": int(request.form.get('age', 30)),
            "gender": request.form.get('gender', 'Unknown'),
            "bloodType": request.form.get('bloodType', 'Unknown'),
            "donorStatus": False,
            "recipientStatus": True,
            "organData": {
                "requiredOrgan": request.form.get('requiredOrgan', 'Unknown'),
                "urgencyScore": int(request.form.get('urgencyScore', 50))
            },
            "medicalHistory": {
                "allergies": request.form.get('allergies', '').split(','),
                "medications": request.form.get('medications', '').split(','),
                "surgeries": request.form.get('surgeries', '').split(','),
                "chronicConditions": request.form.get('chronicConditions', '').split(',')
            },
            "hospitalId": request.form.get('hospitalId', 'HOSPITAL_001'),
            "hospitalName": request.form.get('hospitalName', 'Unknown Hospital'),
            "doctorName": request.form.get('doctorName', 'Unknown Doctor')
        }
        
        # Generate health card
        result = generator.complete_health_card_workflow(recipient_info)
        
        # Return result page
        return render_template('result.html', 
                             card_type="Recipient",
                             health_card=result['health_card'],
                             json_path=os.path.basename(result['json_path']),
                             pdf_path=os.path.basename(result['pdf_path']) if result['pdf_path'] else None,
                             image_path=os.path.basename(result['image_path']) if result['image_path'] else None,
                             ipfs_result=result['ipfs_result'])
    
    # GET request - show form
    return render_template('recipient_form.html')

@app.route('/download/<path:filename>')
def download_file(filename):
    return send_file(os.path.join(app.config['OUTPUT_FOLDER'], filename), as_attachment=True)

@app.route('/view/<path:filename>')
def view_file(filename):
    file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    file_ext = os.path.splitext(filename)[1].lower()
    
    if file_ext == '.pdf':
        return send_file(file_path, mimetype='application/pdf')
    elif file_ext in ['.png', '.jpg', '.jpeg']:
        return send_file(file_path, mimetype=f'image/{file_ext[1:]}')
    elif file_ext == '.json':
        with open(file_path, 'r') as f:
            data = json.load(f)
        return jsonify(data)
    else:
        return send_file(file_path, as_attachment=True)

@app.route('/api/generate-card', methods=['POST'])
def api_generate_card():
    # Get JSON data
    data = request.json
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        # Generate health card
        result = generator.complete_health_card_workflow(data)
        
        # Prepare response
        response = {
            'success': True,
            'health_card': result['health_card'],
            'files': {
                'json': os.path.basename(result['json_path']),
                'pdf': os.path.basename(result['pdf_path']) if result['pdf_path'] else None,
                'image': os.path.basename(result['image_path']) if result['image_path'] else None,
            }
        }
        
        if result['ipfs_result'] and result['ipfs_result'].get('cid'):
            response['ipfs'] = {
                'cid': result['ipfs_result']['cid'],
                'url': result['ipfs_result'].get('url', f"ipfs://{result['ipfs_result']['cid']}")
            }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Run the app
if __name__ == '__main__':
    # Create templates folder if it doesn't exist
    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
    os.makedirs(templates_dir, exist_ok=True)
    
    # Create basic templates if they don't exist
    template_files = {
        'index.html': '''
<!DOCTYPE html>
<html>
<head>
    <title>LifeConnect Health Card Generator</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        h1 {
            color: #2c3e50;
            text-align: center;
        }
        .card-options {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-top: 40px;
        }
        .card-option {
            background-color: #3498db;
            color: white;
            padding: 20px;
            border-radius: 5px;
            text-align: center;
            width: 200px;
            cursor: pointer;
            text-decoration: none;
        }
        .card-option.donor {
            background-color: #27ae60;
        }
        .card-option.recipient {
            background-color: #2980b9;
        }
        .card-option:hover {
            opacity: 0.9;
        }
    </style>
</head>
<body>
    <h1>LifeConnect Health Card Generator</h1>
    <p>Welcome to the LifeConnect Health Card Generator. This tool allows you to create digital health cards for organ donors and recipients.</p>
    
    <div class="card-options">
        <a href="/generate-donor-card" class="card-option donor">
            <h2>Donor Card</h2>
            <p>Generate a health card for an organ donor</p>
        </a>
        
        <a href="/generate-recipient-card" class="card-option recipient">
            <h2>Recipient Card</h2>
            <p>Generate a health card for an organ recipient</p>
        </a>
    </div>
</body>
</html>
        ''',
        
        'donor_form.html': '''
<!DOCTYPE html>
<html>
<head>
    <title>Generate Donor Health Card</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        h1 {
            color: #27ae60;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        input[type="text"], input[type="number"], select {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        .checkbox-group {
            margin-top: 5px;
        }
        .checkbox-group label {
            display: inline-block;
            margin-right: 15px;
            font-weight: normal;
        }
        button {
            background-color: #27ae60;
            color: white;
            border: none;
            padding: 10px 15px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover {
            background-color: #219653;
        }
        a {
            display: inline-block;
            margin-top: 20px;
            color: #2c3e50;
        }
    </style>
</head>
<body>
    <h1>Generate Donor Health Card</h1>
    
    <form method="post">
        <div class="form-group">
            <label for="patientId">Patient ID:</label>
            <input type="text" id="patientId" name="patientId" placeholder="e.g. DONOR_001">
        </div>
        
        <div class="form-group">
            <label for="name">Full Name:</label>
            <input type="text" id="name" name="name" required>
        </div>
        
        <div class="form-group">
            <label for="age">Age:</label>
            <input type="number" id="age" name="age" min="18" required>
        </div>
        
        <div class="form-group">
            <label for="gender">Gender:</label>
            <select id="gender" name="gender">
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Other">Other</option>
            </select>
        </div>
        
        <div class="form-group">
            <label for="bloodType">Blood Type:</label>
            <select id="bloodType" name="bloodType" required>
                <option value="A+">A+</option>
                <option value="A-">A-</option>
                <option value="B+">B+</option>
                <option value="B-">B-</option>
                <option value="AB+">AB+</option>
                <option value="AB-">AB-</option>
                <option value="O+">O+</option>
                <option value="O-">O-</option>
            </select>
        </div>
        
        <div class="form-group">
            <label>Available Organs:</label>
            <div class="checkbox-group">
                <label><input type="checkbox" name="organTypes" value="heart"> Heart</label>
                <label><input type="checkbox" name="organTypes" value="liver"> Liver</label>
                <label><input type="checkbox" name="organTypes" value="kidney"> Kidney</label>
                <label><input type="checkbox" name="organTypes" value="lung"> Lung</label>
                <label><input type="checkbox" name="organTypes" value="pancreas"> Pancreas</label>
            </div>
        </div>
        
        <div class="form-group">
            <label>Consent:</label>
            <div class="checkbox-group">
                <label><input type="checkbox" name="donorConsent" checked> Donor Consent</label>
                <label><input type="checkbox" name="familyConsent"> Family Consent</label>
            </div>
        </div>
        
        <div class="form-group">
            <label for="allergies">Allergies (comma-separated):</label>
            <input type="text" id="allergies" name="allergies" placeholder="e.g. Penicillin, Peanuts">
        </div>
        
        <div class="form-group">
            <label for="medications">Medications (comma-separated):</label>
            <input type="text" id="medications" name="medications" placeholder="e.g. Lisinopril, Metformin">
        </div>
        
        <div class="form-group">
            <label for="hospitalName">Hospital Name:</label>
            <input type="text" id="hospitalName" name="hospitalName" value="City General Hospital">
        </div>
        
        <div class="form-group">
            <label for="doctorName">Doctor Name:</label>
            <input type="text" id="doctorName" name="doctorName" value="Dr. Sarah Johnson">
        </div>
        
        <button type="submit">Generate Health Card</button>
    </form>
    
    <a href="/">Back to Home</a>
</body>
</html>
        ''',
        
        'recipient_form.html': '''
<!DOCTYPE html>
<html>
<head>
    <title>Generate Recipient Health Card</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        h1 {
            color: #2980b9;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        input[type="text"], input[type="number"], select {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        button {
            background-color: #2980b9;
            color: white;
            border: none;
            padding: 10px 15px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover {
            background-color: #2c3e50;
        }
        a {
            display: inline-block;
            margin-top: 20px;
            color: #2c3e50;
        }
    </style>
</head>
<body>
    <h1>Generate Recipient Health Card</h1>
    
    <form method="post">
        <div class="form-group">
            <label for="patientId">Patient ID:</label>
            <input type="text" id="patientId" name="patientId" placeholder="e.g. RECIPIENT_001">
        </div>
        
        <div class="form-group">
            <label for="name">Full Name:</label>
            <input type="text" id="name" name="name" required>
        </div>
        
        <div class="form-group">
            <label for="age">Age:</label>
            <input type="number" id="age" name="age" min="1" required>
        </div>
        
        <div class="form-group">
            <label for="gender">Gender:</label>
            <select id="gender" name="gender">
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Other">Other</option>
            </select>
        </div>
        
        <div class="form-group">
            <label for="bloodType">Blood Type:</label>
            <select id="bloodType" name="bloodType" required>
                <option value="A+">A+</option>
                <option value="A-">A-</option>
                <option value="B+">B+</option>
                <option value="B-">B-</option>
                <option value="AB+">AB+</option>
                <option value="AB-">AB-</option>
                <option value="O+">O+</option>
                <option value="O-">O-</option>
            </select>
        </div>
        
        <div class="form-group">
            <label for="requiredOrgan">Required Organ:</label>
            <select id="requiredOrgan" name="requiredOrgan" required>
                <option value="heart">Heart</option>
                <option value="liver">Liver</option>
                <option value="kidney">Kidney</option>
                <option value="lung">Lung</option>
                <option value="pancreas">Pancreas</option>
            </select>
        </div>
        
        <div class="form-group">
            <label for="urgencyScore">Urgency Score (1-100):</label>
            <input type="number" id="urgencyScore" name="urgencyScore" min="1" max="100" value="75" required>
        </div>
        
        <div class="form-group">
            <label for="allergies">Allergies (comma-separated):</label>
            <input type="text" id="allergies" name="allergies" placeholder="e.g. Penicillin, Peanuts">
        </div>
        
        <div class="form-group">
            <label for="medications">Medications (comma-separated):</label>
            <input type="text" id="medications" name="medications" placeholder="e.g. Lisinopril, Metformin">
        </div>
        
        <div class="form-group">
            <label for="hospitalName">Hospital Name:</label>
            <input type="text" id="hospitalName" name="hospitalName" value="Metro Medical Center">
        </div>
        
        <div class="form-group">
            <label for="doctorName">Doctor Name:</label>
            <input type="text" id="doctorName" name="doctorName" value="Dr. Robert Williams">
        </div>
        
        <button type="submit">Generate Health Card</button>
    </form>
    
    <a href="/">Back to Home</a>
</body>
</html>
        ''',
        
        'result.html': '''
<!DOCTYPE html>
<html>
<head>
    <title>Health Card Generated</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        h1 {
            color: #2c3e50;
        }
        h1.donor {
            color: #27ae60;
        }
        h1.recipient {
            color: #2980b9;
        }
        .card-info {
            background-color: #f9f9f9;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .download-links {
            margin-top: 30px;
        }
        .download-link {
            display: inline-block;
            background-color: #3498db;
            color: white;
            padding: 10px 15px;
            border-radius: 4px;
            text-decoration: none;
            margin-right: 10px;
            margin-bottom: 10px;
        }
        .download-link.json {
            background-color: #f39c12;
        }
        .download-link.pdf {
            background-color: #e74c3c;
        }
        .download-link.image {
            background-color: #9b59b6;
        }
        .download-link.ipfs {
            background-color: #1abc9c;
        }
        .download-link:hover {
            opacity: 0.9;
        }
        .ipfs-info {
            margin-top: 20px;
            padding: 15px;
            background-color: #e8f7f5;
            border-radius: 5px;
        }
        pre {
            background-color: #f8f8f8;
            padding: 10px;
            border-radius: 4px;
            overflow-x: auto;
        }
        a.button {
            display: inline-block;
            background-color: #2c3e50;
            color: white;
            padding: 10px 15px;
            border-radius: 4px;
            text-decoration: none;
            margin-top: 20px;
        }
        a.button:hover {
            background-color: #34495e;
        }
    </style>
</head>
<body>
    <h1 class="{{ card_type.lower() }}">{{ card_type }} Health Card Generated!</h1>
    
    <div class="card-info">
        <h2>Card Information:</h2>
        <p><strong>Patient ID:</strong> {{ health_card.patientId }}</p>
        <p><strong>Name:</strong> {{ health_card.name }}</p>
        <p><strong>Age:</strong> {{ health_card.age }}</p>
        <p><strong>Blood Type:</strong> {{ health_card.bloodType }}</p>
        
        {% if card_type == 'Donor' %}
            <p><strong>Available Organs:</strong> {{ ', '.join(health_card.organData.availableOrgans) }}</p>
            <p><strong>Donor Consent:</strong> {{ 'Yes' if health_card.donorConsent else 'No' }}</p>
            <p><strong>Family Consent:</strong> {{ 'Yes' if health_card.familyConsent else 'No' }}</p>
        {% else %}
            <p><strong>Required Organ:</strong> {{ health_card.organData.requiredOrgan }}</p>
            <p><strong>Urgency Score:</strong> {{ health_card.organData.urgencyScore }}/100</p>
        {% endif %}
        
        <p><strong>Hospital:</strong> {{ health_card.hospitalName }}</p>
        <p><strong>Doctor:</strong> {{ health_card.doctorName }}</p>
        <p><strong>Generated:</strong> {{ health_card.timestamp }}</p>
    </div>
    
    {% if ipfs_result and ipfs_result.cid %}
        <div class="ipfs-info">
            <h2>IPFS Information:</h2>
            <p><strong>IPFS CID:</strong> {{ ipfs_result.cid }}</p>
            {% if ipfs_result.url %}
                <p><strong>IPFS Gateway URL:</strong> <a href="{{ ipfs_result.url }}" target="_blank">{{ ipfs_result.url }}</a></p>
            {% endif %}
            <p>This health card has been permanently stored on the InterPlanetary File System (IPFS), providing an immutable and decentralized record.</p>
        </div>
    {% endif %}
    
    <div class="download-links">
        <h2>Download Files:</h2>
        
        {% if json_path %}
            <a href="/download/{{ json_path }}" class="download-link json">Download JSON</a>
            <a href="/view/{{ json_path }}" class="download-link json" target="_blank">View JSON</a>
        {% endif %}
        
        {% if pdf_path %}
            <a href="/download/{{ pdf_path }}" class="download-link pdf">Download PDF</a>
            <a href="/view/{{ pdf_path }}" class="download-link pdf" target="_blank">View PDF</a>
        {% endif %}
        
        {% if image_path %}
            <a href="/download/{{ image_path }}" class="download-link image">Download Image</a>
            <a href="/view/{{ image_path }}" class="download-link image" target="_blank">View Image</a>
        {% endif %}
    </div>
    
    <a href="/" class="button">Back to Home</a>
</body>
</html>
        '''
    }
    
    for filename, content in template_files.items():
        filepath = os.path.join(templates_dir, filename)
        if not os.path.exists(filepath):
            with open(filepath, 'w') as f:
                f.write(content)
    
    # Start the app
    app.run(debug=True, host='0.0.0.0', port=5000)
