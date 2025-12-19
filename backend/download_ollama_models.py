#!/usr/bin/env python3
"""
Script to download recommended Ollama models for the Academic AI Chat
This script downloads the best models for different use cases
"""
import subprocess
import sys
import time
import io
import os

# Fix encoding for Windows console
if sys.platform == 'win32':
    try:
        # Set UTF-8 encoding for Windows console output
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        # Also set environment variable
        os.environ['PYTHONIOENCODING'] = 'utf-8'
    except:
        pass

# Recommended models for different use cases
RECOMMENDED_MODELS = {
    "fast": {
        "mistral:7b-instruct-q4_0": {
            "name": "Mistral 7B Instruct (Q4)",
            "size": "~4GB",
            "speed": "Very Fast",
            "quality": "Good",
            "best_for": ["general", "qa", "reformulation"],
            "description": "Fast and efficient for general tasks"
        },
        "llama3.2:3b": {
            "name": "Llama 3.2 3B",
            "size": "~2GB",
            "speed": "Extremely Fast",
            "quality": "Good",
            "best_for": ["general", "qa"],
            "description": "Lightweight and very fast"
        }
    },
    "balanced": {
        "mistral:7b-instruct": {
            "name": "Mistral 7B Instruct",
            "size": "~4.1GB",
            "speed": "Fast",
            "quality": "Very Good",
            "best_for": ["general", "qa", "reformulation", "grammar"],
            "description": "Best balance of speed and quality"
        },
        "llama3.1:8b": {
            "name": "Llama 3.1 8B",
            "size": "~4.7GB",
            "speed": "Fast",
            "quality": "Very Good",
            "best_for": ["general", "qa"],
            "description": "Excellent for academic questions"
        }
    },
    "quality": {
        "mistral-nemo:12b": {
            "name": "Mistral Nemo 12B",
            "size": "~7GB",
            "speed": "Medium",
            "quality": "Excellent",
            "best_for": ["qa", "reformulation"],
            "description": "High quality for complex tasks"
        },
        "llama3.1:70b-q4_0": {
            "name": "Llama 3.1 70B (Q4)",
            "size": "~40GB",
            "speed": "Slow",
            "quality": "Excellent",
            "best_for": ["qa", "reformulation"],
            "description": "Best quality, requires powerful hardware"
        }
    }
}

def check_ollama_installed():
    """Check if Ollama is installed and running"""
    try:
        # Use encoding='utf-8' with errors='replace' for Windows compatibility
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False

def download_model(model_name):
    """Download a model using Ollama"""
    print(f"\n📥 Downloading {model_name}...")
    print("   This may take several minutes depending on your internet connection...")
    
    try:
        import sys
        import io
        
        # Fix encoding for Windows
        if sys.platform == 'win32':
            # Use UTF-8 encoding for Windows
            process = subprocess.Popen(
                ["ollama", "pull", model_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1
            )
            
            # Read output with UTF-8 encoding, handle errors gracefully
            decoder = io.TextIOWrapper(process.stdout, encoding='utf-8', errors='replace')
            
            # Stream output
            for line in decoder:
                print(f"   {line.strip()}")
            
            process.wait()
            decoder.close()
        else:
            # Unix/Linux/Mac - use text mode
            process = subprocess.Popen(
                ["ollama", "pull", model_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Stream output
            for line in process.stdout:
                print(f"   {line.strip()}")
            
            process.wait()
        
        if process.returncode == 0:
            print(f"✅ Successfully downloaded {model_name}")
            return True
        else:
            print(f"❌ Failed to download {model_name}")
            return False
    except Exception as e:
        print(f"❌ Error downloading {model_name}: {e}")
        import traceback
        traceback.print_exc()
        return False

def list_installed_models():
    """List currently installed Ollama models"""
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=10
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            models = []
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if parts:
                        models.append(parts[0])
            return models
        return []
    except Exception as e:
        print(f"Error listing models: {e}")
        return []

def main():
    print("=" * 60)
    print("🚀 Academic AI - Ollama Model Downloader")
    print("=" * 60)
    
    # Check if Ollama is installed
    if not check_ollama_installed():
        print("\n❌ Ollama is not installed or not running!")
        print("\nPlease:")
        print("1. Install Ollama from https://ollama.ai")
        print("2. Make sure Ollama is running")
        print("3. Run this script again")
        sys.exit(1)
    
    print("\n✅ Ollama is installed and running")
    
    # List currently installed models
    installed = list_installed_models()
    print(f"\n📋 Currently installed models: {len(installed)}")
    if installed:
        for model in installed:
            print(f"   - {model}")
    
    # Recommended models for different use cases
    print("\n" + "=" * 60)
    print("📦 Recommended Models by Use Case")
    print("=" * 60)
    
    print("\n⚡ FAST MODELS (Best for quick responses):")
    for model_id, info in RECOMMENDED_MODELS["fast"].items():
        status = "✅ Installed" if model_id in installed else "❌ Not installed"
        print(f"   {model_id}")
        print(f"      Name: {info['name']}")
        print(f"      Size: {info['size']} | Speed: {info['speed']} | Quality: {info['quality']}")
        print(f"      Best for: {', '.join(info['best_for'])}")
        print(f"      Status: {status}")
        print()
    
    print("\n⚖️  BALANCED MODELS (Best overall):")
    for model_id, info in RECOMMENDED_MODELS["balanced"].items():
        status = "✅ Installed" if model_id in installed else "❌ Not installed"
        print(f"   {model_id}")
        print(f"      Name: {info['name']}")
        print(f"      Size: {info['size']} | Speed: {info['speed']} | Quality: {info['quality']}")
        print(f"      Best for: {', '.join(info['best_for'])}")
        print(f"      Status: {status}")
        print()
    
    print("\n🎯 QUALITY MODELS (Best for accuracy):")
    for model_id, info in RECOMMENDED_MODELS["quality"].items():
        status = "✅ Installed" if model_id in installed else "❌ Not installed"
        print(f"   {model_id}")
        print(f"      Name: {info['name']}")
        print(f"      Size: {info['size']} | Speed: {info['speed']} | Quality: {info['quality']}")
        print(f"      Best for: {', '.join(info['best_for'])}")
        print(f"      Status: {status}")
        print()
    
    # Ask user which models to download
    print("\n" + "=" * 60)
    print("💾 Download Options")
    print("=" * 60)
    print("\n1. Download recommended fast models (best for speed)")
    print("2. Download recommended balanced models (recommended)")
    print("3. Download all recommended models")
    print("4. Download specific model")
    print("5. Exit")
    
    choice = input("\nEnter your choice (1-5): ").strip()
    
    models_to_download = []
    
    if choice == "1":
        models_to_download = list(RECOMMENDED_MODELS["fast"].keys())
    elif choice == "2":
        models_to_download = list(RECOMMENDED_MODELS["balanced"].keys())
    elif choice == "3":
        models_to_download = (
            list(RECOMMENDED_MODELS["fast"].keys()) +
            list(RECOMMENDED_MODELS["balanced"].keys()) +
            list(RECOMMENDED_MODELS["quality"].keys())
        )
    elif choice == "4":
        print("\nAvailable models:")
        all_models = []
        for category in RECOMMENDED_MODELS.values():
            for model_id, info in category.items():
                all_models.append((model_id, info))
                print(f"   {model_id} - {info['name']}")
        model_input = input("\nEnter model name: ").strip()
        if model_input:
            models_to_download = [model_input]
    elif choice == "5":
        print("\n👋 Goodbye!")
        sys.exit(0)
    else:
        print("\n❌ Invalid choice")
        sys.exit(1)
    
    # Filter out already installed models
    models_to_download = [m for m in models_to_download if m not in installed]
    
    if not models_to_download:
        print("\n✅ All selected models are already installed!")
        sys.exit(0)
    
    print(f"\n📥 Will download {len(models_to_download)} model(s):")
    for model in models_to_download:
        print(f"   - {model}")
    
    confirm = input("\nContinue? (y/n): ").strip().lower()
    if confirm != 'y':
        print("\n❌ Cancelled")
        sys.exit(0)
    
    # Download models
    print("\n" + "=" * 60)
    print("📥 Downloading Models")
    print("=" * 60)
    
    success_count = 0
    for model in models_to_download:
        if download_model(model):
            success_count += 1
        time.sleep(1)  # Small delay between downloads
    
    print("\n" + "=" * 60)
    print("✅ Download Complete!")
    print("=" * 60)
    print(f"\nSuccessfully downloaded: {success_count}/{len(models_to_download)} models")
    print("\n💡 Tip: Restart your backend server to use the new models")
    print("   The models will be available in the chat interface model selector")

if __name__ == "__main__":
    main()

