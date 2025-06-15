import argparse
import json
import os
import sys
from health_card_generator import HealthCardGenerator

def main():
    parser = argparse.ArgumentParser(description='LifeConnect Health Card Generator CLI')
    
    # Define subparsers for different card types
    subparsers = parser.add_subparsers(dest='command', help='Command')
    
    # Donor card parser
    donor_parser = subparsers.add_parser('donor', help='Generate donor health card')
    donor_parser.add_argument('--name', required=True, help='Donor name')
    donor_parser.add_argument('--age', type=int, required=True, help='Donor age')
    donor_parser.add_argument('--blood-type', required=True, help='Blood type (e.g., O+)')
    donor_parser.add_argument('--organs', nargs='+', required=True, help='Available organs (e.g., heart liver kidney)')
    donor_parser.add_argument('--hospital', default='City General Hospital', help='Hospital name')
    donor_parser.add_argument('--doctor', default='Dr. Sarah Johnson', help='Doctor name')
    donor_parser.add_argument('--consent', action='store_true', help='Family consent given')
    donor_parser.add_argument('--output-dir', default='output', help='Output directory')
    donor_parser.add_argument('--no-pdf', action='store_true', help='Skip PDF generation')
    donor_parser.add_argument('--no-image', action='store_true', help='Skip image generation')
    donor_parser.add_argument('--no-ipfs', action='store_true', help='Skip IPFS upload')
    
    # Recipient card parser
    recipient_parser = subparsers.add_parser('recipient', help='Generate recipient health card')
    recipient_parser.add_argument('--name', required=True, help='Recipient name')
    recipient_parser.add_argument('--age', type=int, required=True, help='Recipient age')
    recipient_parser.add_argument('--blood-type', required=True, help='Blood type (e.g., O+)')
    recipient_parser.add_argument('--required-organ', required=True, help='Required organ (e.g., heart)')
    recipient_parser.add_argument('--urgency', type=int, default=75, help='Urgency score (1-100)')
    recipient_parser.add_argument('--hospital', default='Metro Medical Center', help='Hospital name')
    recipient_parser.add_argument('--doctor', default='Dr. Robert Williams', help='Doctor name')
    recipient_parser.add_argument('--output-dir', default='output', help='Output directory')
    recipient_parser.add_argument('--no-pdf', action='store_true', help='Skip PDF generation')
    recipient_parser.add_argument('--no-image', action='store_true', help='Skip image generation')
    recipient_parser.add_argument('--no-ipfs', action='store_true', help='Skip IPFS upload')
    
    # JSON parser - generate from JSON file
    json_parser = subparsers.add_parser('json', help='Generate health card from JSON file')
    json_parser.add_argument('file', help='JSON file containing health card data')
    json_parser.add_argument('--output-dir', default='output', help='Output directory')
    json_parser.add_argument('--no-pdf', action='store_true', help='Skip PDF generation')
    json_parser.add_argument('--no-image', action='store_true', help='Skip image generation')
    json_parser.add_argument('--no-ipfs', action='store_true', help='Skip IPFS upload')
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Initialize generator
    generator = HealthCardGenerator(output_dir=args.output_dir, ipfs_integration=not args.no_ipfs)
    
    if args.command == 'donor':
        # Create donor health card
        donor_info = {
            "name": args.name,
            "age": args.age,
            "bloodType": args.blood_type,
            "donorStatus": True,
            "recipientStatus": False,
            "organTypes": args.organs,
            "donorConsent": True,
            "familyConsent": args.consent,
            "organData": {
                "availableOrgans": args.organs
            },
            "hospitalName": args.hospital,
            "doctorName": args.doctor
        }
        
        # Generate health card
        result = generator.complete_health_card_workflow(
            donor_info, 
            generate_pdf=not args.no_pdf, 
            generate_image=not args.no_image,
            upload_to_ipfs=not args.no_ipfs
        )
        
        print(f"\n✅ Donor Health Card Generated for {args.name}")
        print(f"📋 JSON: {os.path.basename(result['json_path'])}")
        
        if not args.no_pdf and result['pdf_path']:
            print(f"📄 PDF: {os.path.basename(result['pdf_path'])}")
            
        if not args.no_image and result['image_path']:
            print(f"🖼️ Image: {os.path.basename(result['image_path'])}")
            
        if not args.no_ipfs and result['ipfs_result'] and result['ipfs_result'].get('cid'):
            print(f"🔗 IPFS CID: {result['ipfs_result']['cid']}")
            
    elif args.command == 'recipient':
        # Create recipient health card
        recipient_info = {
            "name": args.name,
            "age": args.age,
            "bloodType": args.blood_type,
            "donorStatus": False,
            "recipientStatus": True,
            "organData": {
                "requiredOrgan": args.required_organ,
                "urgencyScore": args.urgency
            },
            "hospitalName": args.hospital,
            "doctorName": args.doctor
        }
        
        # Generate health card
        result = generator.complete_health_card_workflow(
            recipient_info, 
            generate_pdf=not args.no_pdf, 
            generate_image=not args.no_image,
            upload_to_ipfs=not args.no_ipfs
        )
        
        print(f"\n✅ Recipient Health Card Generated for {args.name}")
        print(f"📋 JSON: {os.path.basename(result['json_path'])}")
        
        if not args.no_pdf and result['pdf_path']:
            print(f"📄 PDF: {os.path.basename(result['pdf_path'])}")
            
        if not args.no_image and result['image_path']:
            print(f"🖼️ Image: {os.path.basename(result['image_path'])}")
            
        if not args.no_ipfs and result['ipfs_result'] and result['ipfs_result'].get('cid'):
            print(f"🔗 IPFS CID: {result['ipfs_result']['cid']}")
            
    elif args.command == 'json':
        # Load health card data from JSON file
        try:
            with open(args.file, 'r') as f:
                health_card_data = json.load(f)
                
            # Generate health card
            result = generator.complete_health_card_workflow(
                health_card_data, 
                generate_pdf=not args.no_pdf, 
                generate_image=not args.no_image,
                upload_to_ipfs=not args.no_ipfs
            )
            
            print(f"\n✅ Health Card Generated from JSON file: {args.file}")
            print(f"📋 JSON: {os.path.basename(result['json_path'])}")
            
            if not args.no_pdf and result['pdf_path']:
                print(f"📄 PDF: {os.path.basename(result['pdf_path'])}")
                
            if not args.no_image and result['image_path']:
                print(f"🖼️ Image: {os.path.basename(result['image_path'])}")
                
            if not args.no_ipfs and result['ipfs_result'] and result['ipfs_result'].get('cid'):
                print(f"🔗 IPFS CID: {result['ipfs_result']['cid']}")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return

if __name__ == "__main__":
    main()
