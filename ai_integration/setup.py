"""
Setup script for AI Integration

Installs dependencies and trains initial models.
"""

import subprocess
import sys
import os


def install_dependencies():
    """Install required Python packages."""
    print("📦 Installing dependencies...")
    
    try:
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
        ])
        print("✅ Dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def setup_environment():
    """Set up environment file."""
    print("\n🔧 Setting up environment...")
    
    env_example = """# AI Integration Environment Variables

# OpenAI API Key (for GPT-4 powered log analysis)
# Get your key at: https://platform.openai.com/api-keys
OPENAI_API_KEY=your_openai_key_here

# Anthropic API Key (alternative to OpenAI, for Claude)
# Get your key at: https://console.anthropic.com/
ANTHROPIC_API_KEY=your_anthropic_key_here

# Hugging Face Token (for open-source models)
# Get your token at: https://huggingface.co/settings/tokens
HUGGINGFACE_TOKEN=your_hf_token_here

# GitHub Token (already configured in parent .env)
# This is loaded from parent directory
"""
    
    env_path = '.env.example'
    with open(env_path, 'w') as f:
        f.write(env_example)
    
    print(f"✅ Created {env_path}")
    print("📝 Copy this to .env and add your API keys")


def train_initial_models():
    """Train initial ML models."""
    print("\n🤖 Training initial models...")
    
    try:
        from ai_integration.pattern_classifier import TemplateClassifier
        
        # This will auto-train if no model exists
        classifier = TemplateClassifier()
        
        print("✅ Template classifier trained")
        return True
    except Exception as e:
        print(f"❌ Failed to train models: {e}")
        return False


def create_directories():
    """Create necessary directories."""
    print("\n📁 Creating directories...")
    
    dirs = ['models', 'examples', 'docs', 'output']
    
    for dir_name in dirs:
        os.makedirs(dir_name, exist_ok=True)
        print(f"✅ Created {dir_name}/")


def verify_setup():
    """Verify the setup is complete."""
    print("\n🔍 Verifying setup...")
    
    checks = {
        'Requirements file': os.path.exists('requirements.txt'),
        'Pattern classifier': os.path.exists('pattern_classifier.py'),
        'Log analyzer': os.path.exists('log_analyzer.py'),
        'Test generator': os.path.exists('test_generator.py'),
        'AI assistant': os.path.exists('ai_assistant.py'),
        'Models directory': os.path.exists('models'),
    }
    
    all_passed = True
    for check, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"{status} {check}")
        if not passed:
            all_passed = False
    
    return all_passed


def main():
    """Run the setup process."""
    print("\n" + "="*60)
    print("🚀 AI Integration Setup")
    print("="*60 + "\n")
    
    steps = [
        ("Create directories", create_directories),
        ("Install dependencies", install_dependencies),
        ("Setup environment", setup_environment),
        ("Train initial models", train_initial_models),
        ("Verify setup", verify_setup),
    ]
    
    for step_name, step_func in steps:
        print(f"\n▶️  Step: {step_name}")
        success = step_func()
        
        if success is False:
            print(f"\n❌ Setup failed at: {step_name}")
            print("Please fix the errors and run setup again.")
            return 1
    
    print("\n" + "="*60)
    print("✅ Setup Complete!")
    print("="*60 + "\n")
    
    print("📋 Next Steps:")
    print("1. Copy .env.example to .env")
    print("2. Add your API keys to .env")
    print("3. Run examples: python examples/quick_start.py")
    print("4. Or start interactive: python ai_assistant.py")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
