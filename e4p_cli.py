#!/usr/bin/env python3
"""
E4P CLI - Command Line Interface for Encryption 4 People
Provides easy management commands for the E4P application.
"""

import os
import sys
import subprocess
import json
import time
import signal
import psutil
from pathlib import Path
from typing import Optional, List, Dict, Any
import argparse


class E4PCLI:
    """E4P Command Line Interface."""
    
    def __init__(self):
        self.app_name = "E4P"
        self.process_name = "python"
        self.script_name = "run.py"
        self.config_file = ".env"
        self.log_file = "e4p.log"
        self.pid_file = "e4p.pid"
        
    def print_banner(self):
        """Print the E4P CLI banner."""
        print("🔐 E4P - Encryption 4 People CLI")
        print("=" * 40)
        
    def print_menu(self):
        """Print the main menu."""
        print("\n📋 Available Commands:")
        print("1. Status     - Show application status")
        print("2. Start      - Start the E4P server")
        print("3. Stop       - Stop the E4P server")
        print("4. Restart    - Restart the E4P server")
        print("5. Update     - Update E4P to latest version")
        print("6. Logs       - View application logs")
        print("7. Config     - Edit configuration")
        print("8. Test       - Test application functionality")
        print("9. Install    - Install/Reinstall dependencies")
        print("10. Clean     - Clean temporary files")
        print("11. Help      - Show this help menu")
        print("0. Exit       - Exit CLI")
        print("-" * 40)
        
    def get_pid(self) -> Optional[int]:
        """Get the PID of the running E4P process."""
        try:
            if os.path.exists(self.pid_file):
                with open(self.pid_file, 'r') as f:
                    pid = int(f.read().strip())
                    if psutil.pid_exists(pid):
                        return pid
            return None
        except (ValueError, FileNotFoundError):
            return None
    
    def is_running(self) -> bool:
        """Check if E4P is currently running."""
        pid = self.get_pid()
        if pid is None:
            return False
        
        try:
            process = psutil.Process(pid)
            return process.is_running() and self.script_name in ' '.join(process.cmdline())
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status information."""
        status = {
            "running": self.is_running(),
            "pid": self.get_pid(),
            "port": 8080,
            "config_exists": os.path.exists(self.config_file),
            "log_exists": os.path.exists(self.log_file),
            "uptime": None,
            "memory_usage": None,
            "cpu_usage": None
        }
        
        if status["running"] and status["pid"]:
            try:
                process = psutil.Process(status["pid"])
                status["uptime"] = time.time() - process.create_time()
                status["memory_usage"] = process.memory_info().rss / 1024 / 1024  # MB
                status["cpu_usage"] = process.cpu_percent()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        return status
    
    def show_status(self):
        """Show application status."""
        print("\n📊 E4P Status")
        print("-" * 20)
        
        status = self.get_status()
        
        if status["running"]:
            print("🟢 Status: RUNNING")
            print(f"🆔 PID: {status['pid']}")
            print(f"🌐 Port: {status['port']}")
            print(f"⏱️  Uptime: {self.format_uptime(status['uptime'])}")
            if status["memory_usage"]:
                print(f"💾 Memory: {status['memory_usage']:.1f} MB")
            if status["cpu_usage"]:
                print(f"🖥️  CPU: {status['cpu_usage']:.1f}%")
        else:
            print("🔴 Status: STOPPED")
        
        print(f"📁 Config: {'✅' if status['config_exists'] else '❌'} {self.config_file}")
        print(f"📝 Logs: {'✅' if status['log_exists'] else '❌'} {self.log_file}")
        
        if status["running"]:
            print(f"\n🌐 Access: http://localhost:{status['port']}")
    
    def format_uptime(self, seconds: float) -> str:
        """Format uptime in human readable format."""
        if seconds is None:
            return "Unknown"
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    def start_server(self):
        """Start the E4P server."""
        if self.is_running():
            print("⚠️  E4P is already running!")
            return
        
        print("🚀 Starting E4P server...")
        
        try:
            # Start the server in background
            with open(self.log_file, 'a') as log_file:
                process = subprocess.Popen(
                    [sys.executable, self.script_name],
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    preexec_fn=os.setsid if os.name != 'nt' else None
                )
            
            # Save PID
            with open(self.pid_file, 'w') as f:
                f.write(str(process.pid))
            
            # Wait a moment and check if it started successfully
            time.sleep(2)
            
            if self.is_running():
                print("✅ E4P server started successfully!")
                print(f"🌐 Access: http://localhost:8080")
                print(f"📝 Logs: {self.log_file}")
            else:
                print("❌ Failed to start E4P server. Check logs for details.")
                
        except Exception as e:
            print(f"❌ Error starting server: {e}")
    
    def stop_server(self):
        """Stop the E4P server."""
        if not self.is_running():
            print("⚠️  E4P is not running!")
            return
        
        print("🛑 Stopping E4P server...")
        
        try:
            pid = self.get_pid()
            if pid:
                process = psutil.Process(pid)
                process.terminate()
                
                # Wait for graceful shutdown
                try:
                    process.wait(timeout=10)
                except psutil.TimeoutExpired:
                    # Force kill if it doesn't stop gracefully
                    process.kill()
                
                # Remove PID file
                if os.path.exists(self.pid_file):
                    os.remove(self.pid_file)
                
                print("✅ E4P server stopped successfully!")
            else:
                print("❌ Could not find running process.")
                
        except Exception as e:
            print(f"❌ Error stopping server: {e}")
    
    def restart_server(self):
        """Restart the E4P server."""
        print("🔄 Restarting E4P server...")
        self.stop_server()
        time.sleep(1)
        self.start_server()
    
    def update_application(self):
        """Update E4P to the latest version."""
        print("🔄 Updating E4P...")
        
        if self.is_running():
            print("⚠️  Stopping server for update...")
            self.stop_server()
            time.sleep(2)
        
        try:
            # Pull latest changes
            print("📥 Pulling latest changes...")
            result = subprocess.run(['git', 'pull'], capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"❌ Git pull failed: {result.stderr}")
                return
            
            # Install/update dependencies
            print("📦 Installing dependencies...")
            result = subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"❌ Dependency installation failed: {result.stderr}")
                return
            
            print("✅ E4P updated successfully!")
            print("🚀 Starting server...")
            self.start_server()
            
        except Exception as e:
            print(f"❌ Error updating: {e}")
    
    def show_logs(self, lines: int = 50):
        """Show application logs."""
        if not os.path.exists(self.log_file):
            print("❌ No log file found.")
            return
        
        print(f"\n📝 Last {lines} lines of E4P logs:")
        print("-" * 40)
        
        try:
            with open(self.log_file, 'r') as f:
                log_lines = f.readlines()
                for line in log_lines[-lines:]:
                    print(line.rstrip())
        except Exception as e:
            print(f"❌ Error reading logs: {e}")
    
    def edit_config(self):
        """Edit configuration file."""
        if not os.path.exists(self.config_file):
            print(f"❌ Config file {self.config_file} not found.")
            return
        
        print(f"📝 Opening {self.config_file} for editing...")
        
        # Try to use common editors
        editors = ['nano', 'vim', 'vi', 'code', 'notepad']
        
        for editor in editors:
            if subprocess.run(['which', editor], capture_output=True).returncode == 0:
                subprocess.run([editor, self.config_file])
                return
        
        print("❌ No suitable editor found. Please edit the file manually.")
        print(f"📁 File location: {os.path.abspath(self.config_file)}")
    
    def test_application(self):
        """Test application functionality."""
        print("🧪 Testing E4P application...")
        
        try:
            # Run the test script
            result = subprocess.run([sys.executable, 'test_app.py'], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("✅ All tests passed!")
                print(result.stdout)
            else:
                print("❌ Tests failed!")
                print(result.stderr)
                
        except subprocess.TimeoutExpired:
            print("❌ Tests timed out!")
        except Exception as e:
            print(f"❌ Error running tests: {e}")
    
    def install_dependencies(self):
        """Install/Reinstall dependencies."""
        print("📦 Installing E4P dependencies...")
        
        try:
            result = subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Dependencies installed successfully!")
            else:
                print(f"❌ Installation failed: {result.stderr}")
                
        except Exception as e:
            print(f"❌ Error installing dependencies: {e}")
    
    def clean_temp_files(self):
        """Clean temporary files."""
        print("🧹 Cleaning temporary files...")
        
        temp_dirs = ['/tmp/e4p', 'e4p_temp']
        files_to_clean = [self.log_file, self.pid_file]
        
        cleaned = 0
        
        # Clean temp directories
        for temp_dir in temp_dirs:
            if os.path.exists(temp_dir):
                try:
                    import shutil
                    shutil.rmtree(temp_dir)
                    print(f"✅ Cleaned directory: {temp_dir}")
                    cleaned += 1
                except Exception as e:
                    print(f"⚠️  Could not clean {temp_dir}: {e}")
        
        # Clean files
        for file_path in files_to_clean:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    print(f"✅ Cleaned file: {file_path}")
                    cleaned += 1
                except Exception as e:
                    print(f"⚠️  Could not clean {file_path}: {e}")
        
        if cleaned == 0:
            print("ℹ️  No temporary files to clean.")
        else:
            print(f"✅ Cleaned {cleaned} items.")
    
    def show_help(self):
        """Show help information."""
        print("\n📖 E4P CLI Help")
        print("=" * 20)
        print("E4P CLI provides easy management of the Encryption 4 People application.")
        print("\nCommands:")
        print("• Status  - Show if E4P is running and system info")
        print("• Start   - Start the E4P server")
        print("• Stop    - Stop the E4P server")
        print("• Restart - Restart the E4P server")
        print("• Update  - Update to latest version from GitHub")
        print("• Logs    - View application logs")
        print("• Config  - Edit configuration file")
        print("• Test    - Run application tests")
        print("• Install - Install/update dependencies")
        print("• Clean   - Clean temporary files")
        print("\nFor more information, visit: https://github.com/zZedix/E4P")
    
    def run_interactive(self):
        """Run the interactive CLI."""
        self.print_banner()
        
        while True:
            self.print_menu()
            
            try:
                choice = input("\nEnter your choice (0-11): ").strip()
                
                if choice == '0':
                    print("👋 Goodbye!")
                    break
                elif choice == '1':
                    self.show_status()
                elif choice == '2':
                    self.start_server()
                elif choice == '3':
                    self.stop_server()
                elif choice == '4':
                    self.restart_server()
                elif choice == '5':
                    self.update_application()
                elif choice == '6':
                    self.show_logs()
                elif choice == '7':
                    self.edit_config()
                elif choice == '8':
                    self.test_application()
                elif choice == '9':
                    self.install_dependencies()
                elif choice == '10':
                    self.clean_temp_files()
                elif choice == '11':
                    self.show_help()
                else:
                    print("❌ Invalid choice. Please try again.")
                
                input("\nPress Enter to continue...")
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                input("\nPress Enter to continue...")
    
    def run_command(self, command: str, *args):
        """Run a specific command."""
        if command == 'status':
            self.show_status()
        elif command == 'start':
            self.start_server()
        elif command == 'stop':
            self.stop_server()
        elif command == 'restart':
            self.restart_server()
        elif command == 'update':
            self.update_application()
        elif command == 'logs':
            lines = int(args[0]) if args else 50
            self.show_logs(lines)
        elif command == 'config':
            self.edit_config()
        elif command == 'test':
            self.test_application()
        elif command == 'install':
            self.install_dependencies()
        elif command == 'clean':
            self.clean_temp_files()
        else:
            print(f"❌ Unknown command: {command}")
            print("Run 'E4P --help' for available commands.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='E4P CLI - Manage Encryption 4 People')
    parser.add_argument('command', nargs='?', help='Command to run')
    parser.add_argument('args', nargs='*', help='Command arguments')
    
    args = parser.parse_args()
    
    cli = E4PCLI()
    
    if args.command:
        cli.run_command(args.command, *args.args)
    else:
        cli.run_interactive()


if __name__ == '__main__':
    main()
