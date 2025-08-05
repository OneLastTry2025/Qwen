#!/usr/bin/env python3
"""
Comprehensive Model Analysis for All 14 Qwen Models
Analyzes payload structures and configurations for each model
"""

import requests
import json
import sys

# API base URL
BASE_URL = "https://6778fbf7-4391-4ed6-8b7b-3f4e4a372975.preview.emergentagent.com"

def get_all_models():
    """Get list of all available models"""
    try:
        response = requests.get(f"{BASE_URL}/api/models")
        data = response.json()
        if data.get('success'):
            return data['data']
        return []
    except Exception as e:
        print(f"Error fetching models: {e}")
        return []

def analyze_model_config(model_id):
    """Analyze configuration for a specific model"""
    try:
        response = requests.get(f"{BASE_URL}/api/model-info/{model_id}")
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def test_model_chat(model_id, test_prompt):
    """Test chat functionality for a model"""
    try:
        payload = {
            "prompt": test_prompt,
            "model_name": model_id,
            "use_web_search": False
        }
        response = requests.post(f"{BASE_URL}/api/chat", json=payload, timeout=30)
        return {"success": response.json().get('success', False)}
    except Exception as e:
        return {"success": False, "error": str(e)}

def main():
    print("🔍 COMPREHENSIVE QWEN MODEL ANALYSIS")
    print("=" * 80)
    
    # Get all models
    models = get_all_models()
    if not models:
        print("❌ Failed to fetch models")
        return
    
    print(f"📊 Found {len(models)} models:")
    for i, model in enumerate(models, 1):
        print(f"  {i:2d}. {model['id']} ({model['name']})")
    
    print("\n" + "=" * 80)
    print("🔧 MODEL CONFIGURATION ANALYSIS")
    print("=" * 80)
    
    # Model categories for validation
    expected_categories = {
        "coding": [],
        "reasoning": [], 
        "vision": [],
        "multimodal": [],
        "advanced": [],
        "standard": []
    }
    
    # Test prompts for different categories
    test_prompts = {
        "coding": "Write a Python function to calculate fibonacci",
        "reasoning": "Solve this step by step: If all roses are flowers and some flowers are red, are some roses red?",
        "vision": "Describe what you would see in a typical landscape image",
        "multimodal": "How would you process both text and image inputs together?",
        "advanced": "Explain quantum computing in simple terms",
        "standard": "Hello, how are you today?"
    }
    
    # Analyze each model
    analysis_results = {}
    
    for i, model in enumerate(models, 1):
        model_id = model['id']
        model_name = model['name']
        
        print(f"\n🧠 Model {i}: {model_name}")
        print(f"   ID: {model_id}")
        print("-" * 60)
        
        # Get model configuration
        config_info = analyze_model_config(model_id)
        
        if 'error' in config_info:
            print(f"   ❌ Config Error: {config_info['error']}")
            continue
            
        if not config_info.get('success'):
            print(f"   ❌ Failed to get configuration")
            continue
            
        config = config_info.get('config', {})
        capabilities = config_info.get('capabilities', {})
        recommended = config_info.get('recommended_use', {})
        
        category = config.get('category', 'unknown')
        expected_categories[category].append(model_id)
        
        # Print configuration details
        print(f"   📂 Category: {category.upper()}")
        print(f"   🌡️  Temperature: {config.get('optimal_temperature', 'N/A')}")
        print(f"   📝 Max Tokens: {config.get('max_tokens', 'N/A')}")
        print(f"   🧠 Thinking: {config.get('thinking_enabled', False)}")
        print(f"   📄 Schema: {config.get('output_schema', 'N/A')}")
        
        # Print capabilities
        print(f"   🔧 Capabilities:")
        for cap, enabled in capabilities.items():
            status = "✅" if enabled else "❌"
            print(f"      {status} {cap.replace('_', ' ').title()}")
        
        # Print recommended use
        recommended_uses = [use for use, desc in recommended.items() if desc]
        if recommended_uses:
            print(f"   💡 Best for: {', '.join(recommended_uses)}")
        
        # Test the model with appropriate prompt
        test_prompt = test_prompts.get(category, test_prompts['standard'])
        print(f"   🧪 Testing with: '{test_prompt[:40]}{'...' if len(test_prompt) > 40 else ''}'")
        
        test_result = test_model_chat(model_id, test_prompt)
        if test_result.get('success'):
            print(f"   ✅ Chat Test: PASSED")
        else:
            print(f"   ❌ Chat Test: FAILED - {test_result.get('error', 'Unknown error')}")
        
        # Store analysis
        analysis_results[model_id] = {
            "name": model_name,
            "category": category,
            "config": config,
            "capabilities": capabilities,
            "test_success": test_result.get('success', False)
        }
    
    # Print category summary
    print("\n" + "=" * 80)
    print("📊 CATEGORY DISTRIBUTION")
    print("=" * 80)
    
    for category, model_list in expected_categories.items():
        if model_list:
            print(f"\n🏷️  {category.upper()} ({len(model_list)} models):")
            for model_id in model_list:
                model_name = next(m['name'] for m in models if m['id'] == model_id)
                test_status = "✅" if analysis_results[model_id]['test_success'] else "❌"
                print(f"   {test_status} {model_name}")
    
    # Payload structure analysis
    print("\n" + "=" * 80)
    print("🔧 DYNAMIC PAYLOAD ANALYSIS")
    print("=" * 80)
    
    unique_configs = {}
    for model_id, analysis in analysis_results.items():
        config_key = f"{analysis['category']}-{analysis['config'].get('thinking_enabled', False)}-{analysis['config'].get('output_schema', 'none')}"
        if config_key not in unique_configs:
            unique_configs[config_key] = []
        unique_configs[config_key].append(analysis['name'])
    
    print(f"\n📋 Found {len(unique_configs)} unique payload configurations:")
    
    for i, (config_key, model_names) in enumerate(unique_configs.items(), 1):
        category, thinking, schema = config_key.split('-')
        print(f"\n{i}. Configuration: {category.upper()} | Thinking: {thinking} | Schema: {schema}")
        print(f"   Models using this config ({len(model_names)}):")
        for name in model_names:
            print(f"     • {name}")
    
    # Final summary
    print("\n" + "=" * 80)
    print("📈 ANALYSIS SUMMARY")
    print("=" * 80)
    
    total_models = len(analysis_results)
    working_models = sum(1 for analysis in analysis_results.values() if analysis['test_success'])
    
    print(f"✅ Total Models Analyzed: {total_models}")
    print(f"✅ Working Models: {working_models}")
    print(f"❌ Failed Models: {total_models - working_models}")
    print(f"📊 Success Rate: {(working_models/total_models)*100:.1f}%")
    print(f"🔧 Unique Configurations: {len(unique_configs)}")
    
    if working_models == total_models:
        print(f"\n🎉 ALL MODELS ARE WORKING WITH DYNAMIC PAYLOAD GENERATION!")
    else:
        print(f"\n⚠️  Some models need attention.")
    
    print(f"\n✅ Analysis completed successfully!")

if __name__ == "__main__":
    main()