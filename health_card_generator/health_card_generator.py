import json
import os
import sys
import uuid
import qrcode
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import importlib.util

class HealthCardGenerator:
    def __init__(self, templates_dir=None, output_dir=None, ipfs_integration=True):
        # Setup directories
        self.templates_dir = templates_dir or os.path.join(os.path.dirname(__file__), 'templates')
        self.output_dir = output_dir or os.path.join(os.path.dirname(__file__), 'output')
        
        # Create output directory if it doesn't exist
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
        # IPFS integration settings
        self.ipfs_integration = ipfs_integration
        self.ipfs_uploader = None
        
        if ipfs_integration:
            self._setup_ipfs_integration()
            
        print(f"🏥 HealthCard Generator initialized")
        print(f"   Output directory: {self.output_dir}")
        print(f"   IPFS integration: {'✅ Enabled' if ipfs_integration else '❌ Disabled'}")

    def _setup_ipfs_integration(self):
        """Setup IPFS integration by importing the upload module"""
        try:
            # Add paths to import IPFS scripts
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            ipfs_path = os.path.join(project_root, 'ipfs_scripts')
            
            if ipfs_path not in sys.path:
                sys.path.insert(0, ipfs_path)
            
            # Try to import the Python version
            try:
                from upload_healthcard import uploadHealthCard, retrieveHealthCard
                self.ipfs_uploader = {
                    'upload': uploadHealthCard,
                    'retrieve': retrieveHealthCard,
                    'type': 'python'
                }
                print("✅ IPFS Python integration loaded")
            except ImportError:
                print("⚠️ Python IPFS module not found, trying to load JS module via subprocess")
                import subprocess
                
                # Test if we can call the JS version
                result = subprocess.run(
                    ['node', 'upload_healthcard.js', 'test'],
                    cwd=ipfs_path,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    # Define functions to call JS via subprocess
                    def call_js_uploader(data):
                        # Save data to temp file
                        temp_file = os.path.join(ipfs_path, 'temp_data.json')
                        with open(temp_file, 'w') as f:
                            json.dump(data, f)
                            
                        # Call JS uploader
                        result = subprocess.run(
                            ['node', 'upload_healthcard.js', 'upload'],
                            cwd=ipfs_path,
                            capture_output=True,
                            text=True
                        )
                        
                        # Parse output to get CID
                        if result.returncode == 0:
                            # Very basic extraction (would need more robust parsing)
                            lines = result.stdout.split('\n')
                            cid_line = next((l for l in lines if 'IPFS CID:' in l), None)
                            if cid_line:
                                cid = cid_line.split('IPFS CID:')[1].strip()
                                return {'cid': cid, 'method': 'js'}
                        
                        raise Exception(f"JS upload failed: {result.stderr}")
                    
                    def call_js_retriever(cid):
                        result = subprocess.run(
                            ['node', 'upload_healthcard.js', 'retrieve', cid],
                            cwd=ipfs_path,
                            capture_output=True,
                            text=True
                        )
                        
                        if result.returncode == 0:
                            # Try to extract JSON from output
                            try:
                                start_idx = result.stdout.find('{')
                                end_idx = result.stdout.rfind('}') + 1
                                if start_idx >= 0 and end_idx > start_idx:
                                    json_str = result.stdout[start_idx:end_idx]
                                    data = json.loads(json_str)
                                    return data
                            except:
                                pass
                                
                        raise Exception(f"JS retrieval failed: {result.stderr}")
                    
                    self.ipfs_uploader = {
                        'upload': call_js_uploader,
                        'retrieve': call_js_retriever,
                        'type': 'javascript'
                    }
                    print("✅ IPFS JavaScript integration loaded")
                else:
                    print("⚠️ IPFS integration not available")
                    self.ipfs_integration = False
                
        except Exception as e:
            print(f"⚠️ IPFS integration error: {str(e)}")
            self.ipfs_integration = False

    def generate_health_card(self, patient_info):
        """Generate a comprehensive health card JSON structure"""
        # Create a standardized health card
        health_card = {
            # Patient Identity
            "patientId": patient_info.get("patientId", f"PATIENT_{str(uuid.uuid4())[:8]}"),
            "name": patient_info.get("name", "Unknown"),
            "age": patient_info.get("age", 0),
            "gender": patient_info.get("gender", "Unknown"),
            "bloodType": patient_info.get("bloodType", "Unknown"),
            "contactInfo": patient_info.get("contactInfo", {}),
            "address": patient_info.get("address", "Unknown"),
            
            # Donor/Recipient Status
            "donorStatus": patient_info.get("donorStatus", False),
            "recipientStatus": patient_info.get("recipientStatus", False),
            "organTypes": patient_info.get("organTypes", []),
            "donorConsent": patient_info.get("donorConsent", False),
            "familyConsent": patient_info.get("familyConsent", False),
            
            # Medical History
            "medicalHistory": patient_info.get("medicalHistory", {
                "allergies": [],
                "medications": [],
                "surgeries": [],
                "chronicConditions": []
            }),
            
            # Organ Data
            "organData": patient_info.get("organData", {
                "availableOrgans": [],
                "organHealth": {},
                "requiredOrgan": None,
                "urgencyScore": 0
            }),
            
            # Laboratory Results
            "labResults": patient_info.get("labResults", {
                "bloodTests": {},
                "viralScreening": {},
                "tissueTyping": {}
            }),
            
            # Medical Provider Information
            "hospitalId": patient_info.get("hospitalId", "UNKNOWN"),
            "hospitalName": patient_info.get("hospitalName", "Unknown Hospital"),
            "doctorName": patient_info.get("doctorName", "Unknown Doctor"),
            "doctorSignature": patient_info.get("doctorSignature", ""),
            
            # Metadata
            "timestamp": datetime.now().isoformat(),
            "version": "2.0",
            "blockchainAddress": patient_info.get("blockchainAddress", ""),
            "ipfsHash": None  # Will be filled if uploaded to IPFS
        }
        
        return health_card

    def save_health_card(self, health_card, filename=None):
        """Save health card to JSON file"""
        if filename is None:
            filename = f"{health_card['patientId']}_{int(datetime.now().timestamp())}.json"
            
        file_path = os.path.join(self.output_dir, filename)
        
        with open(file_path, 'w') as f:
            json.dump(health_card, f, indent=2)
            
        print(f"✅ Health card saved to: {file_path}")
        return file_path

    def upload_to_ipfs(self, health_card):
        """Upload health card to IPFS with better error handling"""
        if not self.ipfs_integration or not self.ipfs_uploader:
            print("⚠️ IPFS integration not available")
            return None
            
        try:
            print(f"📤 Uploading health card to IPFS...")
            print(f"   Patient: {health_card.get('name', 'Unknown')}")
            print(f"   Patient ID: {health_card.get('patientId', 'Unknown')}")
            
            # Create a clean copy for IPFS upload to ensure data consistency
            ipfs_data = health_card.copy()
            
            # Ensure timestamp is current
            ipfs_data['ipfsUploadTime'] = datetime.now().isoformat()
            
            result = self.ipfs_uploader['upload'](ipfs_data)
            
            if result and result.get('cid'):
                print(f"✅ Health card uploaded to IPFS: {result['cid']}")
                
                # Update original health card with IPFS hash
                health_card['ipfsHash'] = result['cid']
                health_card['ipfsUploadTime'] = ipfs_data['ipfsUploadTime']
                
                return result
            else:
                print("❌ IPFS upload failed - no CID returned")
                return None
                
        except Exception as e:
            print(f"❌ IPFS upload error: {str(e)}")
            return None

    def retrieve_from_ipfs(self, cid):
        """Retrieve health card from IPFS"""
        if not self.ipfs_integration or not self.ipfs_uploader:
            print("⚠️ IPFS integration not available")
            return None
            
        try:
            print(f"📥 Retrieving health card from IPFS: {cid}")
            return self.ipfs_uploader['retrieve'](cid)
        except Exception as e:
            print(f"❌ IPFS retrieval error: {str(e)}")
            return None

    def generate_qr_code(self, data, filename=None):
        """Generate QR code for health card data"""
        if isinstance(data, dict):
            # If data is a health card, use the ID or IPFS hash
            if 'ipfsHash' in data and data['ipfsHash']:
                qr_data = f"ipfs://{data['ipfsHash']}"
            else:
                qr_data = f"id:{data['patientId']}"
        else:
            # Use data directly (e.g., IPFS CID)
            qr_data = data
            
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Save if filename provided
        if filename:
            file_path = os.path.join(self.output_dir, filename)
            qr_img.save(file_path)
            print(f"✅ QR code saved to: {file_path}")
            
        return qr_img

    def generate_pdf_card(self, health_card, filename=None, include_qr=True):
        """Generate a PDF health card"""
        if filename is None:
            filename = f"{health_card['patientId']}_card_{int(datetime.now().timestamp())}.pdf"
            
        file_path = os.path.join(self.output_dir, filename)
        
        # Create PDF document
        doc = SimpleDocTemplate(
            file_path,
            pagesize=A4,
            rightMargin=72, leftMargin=72,
            topMargin=72, bottomMargin=72
        )
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            name='Title',
            parent=styles['Heading1'],
            alignment=TA_CENTER,
            fontSize=16,
            spaceAfter=0.25*inch
        )
        subtitle_style = ParagraphStyle(
            name='Subtitle', 
            parent=styles['Heading2'],
            alignment=TA_CENTER,
            fontSize=14,
            spaceAfter=0.25*inch
        )
        header_style = ParagraphStyle(
            name='Header',
            parent=styles['Heading3'],
            fontSize=12,
            spaceAfter=0.1*inch
        )
        normal_style = styles["Normal"]
        
        # Story (elements to add)
        story = []
        
        # Card type (Donor or Recipient)
        card_type = "DONOR" if health_card.get('donorStatus', False) else "RECIPIENT"
        
        # Title
        story.append(Paragraph(f"LIFECONNECT HEALTH CARD", title_style))
        story.append(Paragraph(f"{card_type} CARD", subtitle_style))
        story.append(Spacer(1, 0.2*inch))
        
        # QR Code
        if include_qr:
            # Generate QR code with health card data or IPFS hash
            qr_img = self.generate_qr_code(health_card)
            qr_path = os.path.join(self.output_dir, f"temp_qr_{health_card['patientId']}.png")
            qr_img.save(qr_path)
            
            # Add QR code to PDF
            qr_img_size = 1.5*inch
            story.append(RLImage(qr_path, width=qr_img_size, height=qr_img_size))
            story.append(Spacer(1, 0.1*inch))
            
            # Add IPFS info if available
            if health_card.get('ipfsHash'):
                story.append(Paragraph(f"IPFS: {health_card['ipfsHash'][:16]}...", normal_style))
            
            story.append(Spacer(1, 0.2*inch))
        
        # Patient Information Table
        patient_data = [
            ["Patient ID:", health_card['patientId']],
            ["Name:", health_card['name']],
            ["Age:", str(health_card['age'])],
            ["Blood Type:", health_card['bloodType']]
        ]
        
        if card_type == "DONOR":
            available_organs = ", ".join(health_card.get('organData', {}).get('availableOrgans', []))
            patient_data.append(["Available Organs:", available_organs])
        else:
            required_organ = health_card.get('organData', {}).get('requiredOrgan', 'Unknown')
            urgency = health_card.get('organData', {}).get('urgencyScore', 0)
            patient_data.append(["Required Organ:", required_organ])
            patient_data.append(["Urgency Score:", f"{urgency}/100"])
        
        # Create table
        patient_table = Table(patient_data, colWidths=[1.5*inch, 3*inch])
        patient_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        
        story.append(Paragraph("Patient Information", header_style))
        story.append(patient_table)
        story.append(Spacer(1, 0.2*inch))
        
        # Medical Information Section
        if card_type == "DONOR":
            story.append(Paragraph("Donor Information", header_style))
            
            # Consent info
            consent_data = [
                ["Donor Consent:", "Yes" if health_card.get('donorConsent', False) else "No"],
                ["Family Consent:", "Yes" if health_card.get('familyConsent', False) else "No"],
                ["Registration Date:", health_card.get('timestamp', 'Unknown').split('T')[0]]
            ]
            
            consent_table = Table(consent_data, colWidths=[1.5*inch, 3*inch])
            consent_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey)
            ]))
            
            story.append(consent_table)
            story.append(Spacer(1, 0.2*inch))
        else:
            # Recipient specific info
            story.append(Paragraph("Recipient Medical Status", header_style))
            
            # Add appropriate recipient data
            medical_data = [
                ["Required Organ:", health_card.get('organData', {}).get('requiredOrgan', 'Unknown')],
                ["Urgency Score:", f"{health_card.get('organData', {}).get('urgencyScore', 0)}/100"],
                ["Registration Date:", health_card.get('timestamp', 'Unknown').split('T')[0]]
            ]
            
            medical_table = Table(medical_data, colWidths=[1.5*inch, 3*inch])
            medical_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey)
            ]))
            
            story.append(medical_table)
            story.append(Spacer(1, 0.2*inch))
        
        # Hospital Information
        story.append(Paragraph("Medical Provider Information", header_style))
        
        hospital_data = [
            ["Hospital:", health_card.get('hospitalName', 'Unknown Hospital')],
            ["Hospital ID:", health_card.get('hospitalId', 'Unknown')],
            ["Doctor:", health_card.get('doctorName', 'Unknown Doctor')]
        ]
        
        hospital_table = Table(hospital_data, colWidths=[1.5*inch, 3*inch])
        hospital_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        
        story.append(hospital_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Footer
        story.append(Paragraph("This health card is part of the LifeConnect Organ Donation System.", normal_style))
        story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
        
        # Build PDF
        doc.build(story)
        
        # Clean up temporary files
        if include_qr and os.path.exists(qr_path):
            os.remove(qr_path)
        
        print(f"✅ PDF health card generated: {file_path}")
        return file_path

    def generate_image_card(self, health_card, filename=None, size=(1050, 600), include_qr=True):
        """Generate an image health card (PNG format)"""
        if filename is None:
            filename = f"{health_card['patientId']}_card_{int(datetime.now().timestamp())}.png"
            
        file_path = os.path.join(self.output_dir, filename)
        
        # Create blank image
        background_color = (255, 255, 255)
        img = Image.new('RGB', size, color=background_color)
        draw = ImageDraw.Draw(img)
        
        # Try to load fonts, fall back to default if not available
        try:
            title_font = ImageFont.truetype("arial.ttf", 36)
            header_font = ImageFont.truetype("arial.ttf", 24)
            normal_font = ImageFont.truetype("arial.ttf", 18)
            small_font = ImageFont.truetype("arial.ttf", 14)
        except IOError:
            # Use default font
            title_font = ImageFont.load_default()
            header_font = ImageFont.load_default()
            normal_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # Card type (Donor or Recipient)
        card_type = "DONOR" if health_card.get('donorStatus', False) else "RECIPIENT"
        card_color = (0, 128, 0) if card_type == "DONOR" else (0, 0, 192)  # Green for donor, Blue for recipient
        
        # Draw header background
        draw.rectangle([(0, 0), (size[0], 80)], fill=card_color)
        
        # Draw title
        draw.text((size[0]//2, 40), "LIFECONNECT HEALTH CARD", font=title_font, fill=(255, 255, 255), anchor="mm")
        draw.text((size[0]//2, 120), f"{card_type} CARD", font=header_font, fill=card_color, anchor="mm")
        
        # Draw QR code if requested
        if include_qr:
            qr_img = self.generate_qr_code(health_card)
            qr_size = 150
            qr_img = qr_img.resize((qr_size, qr_size))
            qr_position = (size[0] - qr_size - 50, 150)
            img.paste(qr_img, qr_position)
        
        # Draw patient info
        draw.text((50, 170), "Patient Information:", font=header_font, fill=(0, 0, 0))
        draw.text((50, 210), f"Patient ID: {health_card['patientId']}", font=normal_font, fill=(0, 0, 0))
        draw.text((50, 240), f"Name: {health_card['name']}", font=normal_font, fill=(0, 0, 0))
        draw.text((50, 270), f"Age: {health_card['age']}", font=normal_font, fill=(0, 0, 0))
        draw.text((50, 300), f"Blood Type: {health_card['bloodType']}", font=normal_font, fill=(0, 0, 0))
        
        # Draw specific info based on card type
        if card_type == "DONOR":
            available_organs = ", ".join(health_card.get('organData', {}).get('availableOrgans', []))
            draw.text((50, 350), "Donor Information:", font=header_font, fill=(0, 0, 0))
            draw.text((50, 390), f"Available Organs: {available_organs}", font=normal_font, fill=(0, 0, 0))
            draw.text((50, 420), f"Donor Consent: {'Yes' if health_card.get('donorConsent', False) else 'No'}", font=normal_font, fill=(0, 0, 0))
            draw.text((50, 450), f"Family Consent: {'Yes' if health_card.get('familyConsent', False) else 'No'}", font=normal_font, fill=(0, 0, 0))
        else:
            required_organ = health_card.get('organData', {}).get('requiredOrgan', 'Unknown')
            urgency = health_card.get('organData', {}).get('urgencyScore', 0)
            draw.text((50, 350), "Recipient Information:", font=header_font, fill=(0, 0, 0))
            draw.text((50, 390), f"Required Organ: {required_organ}", font=normal_font, fill=(0, 0, 0))
            draw.text((50, 420), f"Urgency Score: {urgency}/100", font=normal_font, fill=(0, 0, 0))
        
        # Draw hospital info
        draw.text((50, 500), f"Hospital: {health_card.get('hospitalName', 'Unknown Hospital')}", font=normal_font, fill=(0, 0, 0))
        draw.text((50, 530), f"Doctor: {health_card.get('doctorName', 'Unknown Doctor')}", font=normal_font, fill=(0, 0, 0))
        
        # Draw footer
        draw.text((size[0]//2, size[1]-30), f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", font=small_font, fill=(128, 128, 128), anchor="mm")
        
        # Save image
        img.save(file_path)
        print(f"✅ Image health card generated: {file_path}")
        return file_path

    def complete_health_card_workflow(self, patient_info, generate_pdf=True, generate_image=True, upload_to_ipfs=True):
        """Complete workflow: Generate, save, create PDF/image cards, and upload to IPFS"""
        # 1. Generate health card JSON
        health_card = self.generate_health_card(patient_info)
        
        # 2. Save health card locally
        json_path = self.save_health_card(health_card)
        
        # 3. Upload to IPFS if requested
        ipfs_result = None
        if upload_to_ipfs and self.ipfs_integration:
            ipfs_result = self.upload_to_ipfs(health_card)
            if ipfs_result and ipfs_result.get('cid'):
                # Update health card with IPFS hash
                health_card['ipfsHash'] = ipfs_result['cid']
                # Re-save with updated IPFS hash
                self.save_health_card(health_card, os.path.basename(json_path))
        
        # 4. Generate PDF if requested
        pdf_path = None
        if generate_pdf:
            pdf_path = self.generate_pdf_card(health_card)
        
        # 5. Generate image if requested
        image_path = None
        if generate_image:
            image_path = self.generate_image_card(health_card)
        
        # Return all results
        return {
            'health_card': health_card,
            'json_path': json_path,
            'pdf_path': pdf_path,
            'image_path': image_path,
            'ipfs_result': ipfs_result
        }

# Main function to test the class
def test_health_card_generator():
    generator = HealthCardGenerator()
    
    # Test with donor data
    donor_info = {
        "patientId": "DONOR_001",
        "name": "John Doe",
        "age": 35,
        "gender": "Male",
        "bloodType": "O+",
        "donorStatus": True,
        "recipientStatus": False,
        "organTypes": ["heart", "liver", "kidneys"],
        "donorConsent": True,
        "familyConsent": True,
        "medicalHistory": {
            "allergies": ["None"],
            "medications": ["None"],
            "surgeries": ["Appendectomy - 2015"],
            "chronicConditions": []
        },
        "organData": {
            "availableOrgans": ["heart", "liver", "kidneys"],
            "organHealth": {
                "heart": "Excellent",
                "liver": "Good",
                "kidneys": "Excellent"
            }
        },
        "labResults": {
            "bloodTests": {
                "hemoglobin": "14.5 g/dL",
                "whiteBloodCells": "7,200/μL",
                "platelets": "250,000/μL"
            },
            "viralScreening": {
                "hiv": "Negative",
                "hepatitisB": "Negative",
                "hepatitisC": "Negative"
            }
        },
        "hospitalId": "HOSPITAL_001",
        "hospitalName": "City General Hospital",
        "doctorName": "Dr. Sarah Johnson, MD"
    }
    
    # Test complete workflow
    print("\n🧪 Testing Donor Health Card Generation...")
    donor_result = generator.complete_health_card_workflow(donor_info)
    
    # Test with recipient data
    recipient_info = {
        "patientId": "RECIPIENT_001",
        "name": "Jane Smith",
        "age": 42,
        "gender": "Female",
        "bloodType": "A+",
        "donorStatus": False,
        "recipientStatus": True,
        "organData": {
            "requiredOrgan": "heart",
            "urgencyScore": 85
        },
        "hospitalId": "HOSPITAL_002",
        "hospitalName": "Metro Medical Center",
        "doctorName": "Dr. Robert Williams, MD"
    }
    
    print("\n🧪 Testing Recipient Health Card Generation...")
    recipient_result = generator.complete_health_card_workflow(recipient_info)
    
    print("\n✅ Health Card Testing Complete!")
    print(f"📂 Files generated in: {generator.output_dir}")
    
    return donor_result, recipient_result

# Run test if script is executed directly
if __name__ == "__main__":
    test_health_card_generator()
