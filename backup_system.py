import os
import shutil
import json
import sqlite3
from datetime import datetime
import subprocess
import zipfile

class BackupManager:
    def __init__(self, base_dir='.'):
        self.base_dir = base_dir
        self.backup_dir = os.path.join(base_dir, 'backups')
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def create_full_backup(self):
        """Create complete system backup"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"lifeconnect_backup_{timestamp}"
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        print(f"🔄 Creating full backup: {backup_name}")
        
        try:
            # Create backup directory
            os.makedirs(backup_path, exist_ok=True)
            
            # Backup database
            self._backup_database(backup_path)
            
            # Backup health cards
            self._backup_health_cards(backup_path)
            
            # Backup configuration files
            self._backup_configs(backup_path)
            
            # Backup smart contracts
            self._backup_contracts(backup_path)
            
            # Create backup manifest
            self._create_manifest(backup_path, timestamp)
            
            # Compress backup
            zip_path = f"{backup_path}.zip"
            self._compress_backup(backup_path, zip_path)
            
            # Remove uncompressed backup
            shutil.rmtree(backup_path)
            
            print(f"✅ Backup created successfully: {zip_path}")
            return zip_path
            
        except Exception as e:
            print(f"❌ Backup failed: {str(e)}")
            return None
    
    def _backup_database(self, backup_path):
        """Backup SQLite database"""
        db_path = os.path.join('backend_api', 'instance', 'lifeconnect.db')
        if os.path.exists(db_path):
            backup_db_path = os.path.join(backup_path, 'database')
            os.makedirs(backup_db_path, exist_ok=True)
            shutil.copy2(db_path, os.path.join(backup_db_path, 'lifeconnect.db'))
            print("✅ Database backed up")
    
    def _backup_health_cards(self, backup_path):
        """Backup generated health cards"""
        health_cards_dir = os.path.join('health_card_generator', 'output')
        if os.path.exists(health_cards_dir):
            backup_health_path = os.path.join(backup_path, 'health_cards')
            shutil.copytree(health_cards_dir, backup_health_path)
            print("✅ Health cards backed up")
    
    def _backup_configs(self, backup_path):
        """Backup configuration files"""
        config_files = [
            'frontend/.env',
            'backend_api/.env',
            'ai_engine/.env',
            'logistics_engine/.env',
            'ipfs_scripts/.env',
            'blockchain/.env'
        ]
        
        config_backup_path = os.path.join(backup_path, 'configs')
        os.makedirs(config_backup_path, exist_ok=True)
        
        for config_file in config_files:
            if os.path.exists(config_file):
                shutil.copy2(config_file, config_backup_path)
        
        print("✅ Configurations backed up")
    
    def _backup_contracts(self, backup_path):
        """Backup smart contracts and deployment info"""
        contract_dirs = [
            'blockchain/contracts',
            'blockchain/artifacts',
            'blockchain/abis'
        ]
        
        contract_files = [
            'blockchain/deployed-contracts.json',
            'integration-contracts.json'
        ]
        
        contracts_backup_path = os.path.join(backup_path, 'blockchain')
        os.makedirs(contracts_backup_path, exist_ok=True)
        
        # Backup directories
        for contract_dir in contract_dirs:
            if os.path.exists(contract_dir):
                dir_name = os.path.basename(contract_dir)
                shutil.copytree(contract_dir, os.path.join(contracts_backup_path, dir_name))
        
        # Backup files
        for contract_file in contract_files:
            if os.path.exists(contract_file):
                shutil.copy2(contract_file, contracts_backup_path)
        
        print("✅ Smart contracts backed up")
    
    def _create_manifest(self, backup_path, timestamp):
        """Create backup manifest"""
        manifest = {
            'backup_timestamp': timestamp,
            'system_version': '1.0.0',
            'components': [
                'database',
                'health_cards', 
                'configurations',
                'smart_contracts'
            ],
            'backup_size': self._get_directory_size(backup_path),
            'files_count': self._count_files(backup_path)
        }
        
        manifest_path = os.path.join(backup_path, 'backup_manifest.json')
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        print("✅ Backup manifest created")
    
    def _compress_backup(self, backup_path, zip_path):
        """Compress backup directory"""
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(backup_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_path = os.path.relpath(file_path, backup_path)
                    zipf.write(file_path, arc_path)
        
        print("✅ Backup compressed")
    
    def _get_directory_size(self, path):
        """Get directory size in MB"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                total_size += os.path.getsize(filepath)
        return round(total_size / (1024 * 1024), 2)  # Convert to MB
    
    def _count_files(self, path):
        """Count files in directory"""
        count = 0
        for root, dirs, files in os.walk(path):
            count += len(files)
        return count
    
    def list_backups(self):
        """List available backups"""
        backups = []
        for filename in os.listdir(self.backup_dir):
            if filename.endswith('.zip') and filename.startswith('lifeconnect_backup_'):
                backup_path = os.path.join(self.backup_dir, filename)
                stat = os.stat(backup_path)
                
                backups.append({
                    'filename': filename,
                    'path': backup_path,
                    'size_mb': round(stat.st_size / (1024 * 1024), 2),
                    'created': datetime.fromtimestamp(stat.st_ctime).isoformat()
                })
        
        return sorted(backups, key=lambda x: x['created'], reverse=True)
    
    def restore_backup(self, backup_filename):
        """Restore from backup"""
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        if not os.path.exists(backup_path):
            print(f"❌ Backup file not found: {backup_filename}")
            return False
        
        print(f"🔄 Restoring from backup: {backup_filename}")
        
        try:
            # Extract backup
            extract_path = os.path.join(self.backup_dir, 'restore_temp')
            if os.path.exists(extract_path):
                shutil.rmtree(extract_path)
            
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                zipf.extractall(extract_path)
            
            # Restore components
            self._restore_database(extract_path)
            self._restore_health_cards(extract_path)
            self._restore_configs(extract_path)
            self._restore_contracts(extract_path)
            
            # Cleanup
            shutil.rmtree(extract_path)
            
            print("✅ Backup restored successfully")
            return True
            
        except Exception as e:
            print(f"❌ Restore failed: {str(e)}")
            return False
    
    def _restore_database(self, extract_path):
        """Restore database"""
        backup_db = os.path.join(extract_path, 'database', 'lifeconnect.db')
        if os.path.exists(backup_db):
            db_dir = os.path.join('backend_api', 'instance')
            os.makedirs(db_dir, exist_ok=True)
            shutil.copy2(backup_db, os.path.join(db_dir, 'lifeconnect.db'))
            print("✅ Database restored")
    
    def _restore_health_cards(self, extract_path):
        """Restore health cards"""
        backup_health = os.path.join(extract_path, 'health_cards')
        if os.path.exists(backup_health):
            health_output_dir = os.path.join('health_card_generator', 'output')
            if os.path.exists(health_output_dir):
                shutil.rmtree(health_output_dir)
            shutil.copytree(backup_health, health_output_dir)
            print("✅ Health cards restored")
    
    def _restore_configs(self, extract_path):
        """Restore configurations"""
        backup_configs = os.path.join(extract_path, 'configs')
        if os.path.exists(backup_configs):
            for config_file in os.listdir(backup_configs):
                # Find original location and restore
                src = os.path.join(backup_configs, config_file)
                # This is simplified - in production, you'd want more sophisticated mapping
                if os.path.basename(src) == '.env':
                    print(f"⚠️ Config restore skipped: {config_file} (manual review recommended)")
            print("✅ Configurations processed (manual review recommended)")
    
    def _restore_contracts(self, extract_path):
        """Restore smart contracts"""
        backup_contracts = os.path.join(extract_path, 'blockchain')
        if os.path.exists(backup_contracts):
            # Copy deployment info
            for filename in ['deployed-contracts.json']:
                src = os.path.join(backup_contracts, filename)
                if os.path.exists(src):
                    shutil.copy2(src, filename)
            print("✅ Contract deployment info restored")

def main():
    """CLI for backup management"""
    import sys
    
    backup_manager = BackupManager()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python backup_system.py backup     - Create backup")
        print("  python backup_system.py list       - List backups")
        print("  python backup_system.py restore <filename> - Restore backup")
        return
    
    command = sys.argv[1]
    
    if command == 'backup':
        backup_manager.create_full_backup()
    elif command == 'list':
        backups = backup_manager.list_backups()
        print(f"\n📋 Available backups ({len(backups)}):")
        for backup in backups:
            print(f"  📦 {backup['filename']} ({backup['size_mb']} MB) - {backup['created']}")
    elif command == 'restore':
        if len(sys.argv) < 3:
            print("❌ Please provide backup filename")
            return
        backup_filename = sys.argv[2]
        backup_manager.restore_backup(backup_filename)

if __name__ == "__main__":
    main()
