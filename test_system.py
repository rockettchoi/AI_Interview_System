#!/usr/bin/env python3
"""
Simple test script to validate the Flask application structure
"""

import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")
    try:
        import fastapi
        print("✅ FastAPI imported successfully")
        
        import openai
        print("✅ OpenAI imported successfully")
        
        from dotenv import load_dotenv
        print("✅ python-dotenv imported successfully")
        
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_app_structure():
    """Test that the app module can be imported"""
    print("\nTesting app structure...")
    try:
        # Set dummy environment variables to avoid API key errors
        os.environ['OPENAI_API_KEY'] = 'test-key'
        os.environ['FLASK_SECRET_KEY'] = 'test-secret'
        
        import app
        print("✅ App module imported successfully")
        
        # Check if FastAPI app is created
        if hasattr(app, 'app'):
            print("✅ FastAPI app instance found")
        else:
            print("❌ FastAPI app instance not found")
            return False
        
        # Check routes
        routes = [route.path for route in app.app.routes]
        expected_routes = ['/', '/start_interview', '/submit_answer', '/results']
        
        for route in expected_routes:
            if route in routes:
                print(f"✅ Route '{route}' registered")
            else:
                print(f"❌ Route '{route}' not found")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_template_files():
    """Test that template files exist"""
    print("\nTesting template files...")
    templates = ['index.html', 'results.html', 'error.html']
    all_exist = True
    
    for template in templates:
        path = f'templates/{template}'
        if os.path.exists(path):
            print(f"✅ Template '{template}' exists")
        else:
            print(f"❌ Template '{template}' not found")
            all_exist = False
    
    return all_exist

def test_static_files():
    """Test that static files exist"""
    print("\nTesting static files...")
    static_files = ['css/style.css', 'js/main.js']
    all_exist = True
    
    for file in static_files:
        path = f'static/{file}'
        if os.path.exists(path):
            print(f"✅ Static file '{file}' exists")
        else:
            print(f"❌ Static file '{file}' not found")
            all_exist = False
    
    return all_exist

def main():
    """Run all tests"""
    print("=" * 50)
    print("AI Mock Interview System - Test Suite")
    print("=" * 50)
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("App Structure", test_app_structure()))
    results.append(("Template Files", test_template_files()))
    results.append(("Static Files", test_static_files()))
    
    print("\n" + "=" * 50)
    print("Test Results Summary")
    print("=" * 50)
    
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All tests passed!")
        print("=" * 50)
        return 0
    else:
        print("❌ Some tests failed")
        print("=" * 50)
        return 1

if __name__ == '__main__':
    sys.exit(main())
