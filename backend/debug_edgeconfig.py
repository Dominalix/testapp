import os
import requests
import json

def test_edge_config():
    print("=== Edge Config Debug ===")
    
    # Get environment variable
    edge_db_url = os.environ.get('EDGE_DB')
    print(f"EDGE_DB env var: {edge_db_url}")
    
    if not edge_db_url:
        print("❌ EDGE_DB environment variable not found")
        return False
    
    try:
        # Parse URL
        if '?' in edge_db_url:
            base_url, params = edge_db_url.split('?', 1)
            edge_config_id = base_url.split('/')[-1]
            token_param = [p for p in params.split('&') if p.startswith('token=')]
            edge_config_token = token_param[0].split('=')[1] if token_param else None
        else:
            edge_config_id = edge_db_url.split('/')[-1]
            edge_config_token = None
        
        print(f"Edge Config ID: {edge_config_id}")
        print(f"Token: {edge_config_token[:20]}..." if edge_config_token else "No token")
        
        # Test read
        headers = {}
        if edge_config_token:
            headers['Authorization'] = f'Bearer {edge_config_token}'
        
        read_url = f'https://api.vercel.com/v1/edge-config/{edge_config_id}/item/app_data'
        print(f"Read URL: {read_url}")
        print(f"Headers: {headers}")
        
        response = requests.get(read_url, headers=headers)
        print(f"Response status: {response.status_code}")
        print(f"Response text: {response.text[:500]}...")
        
        if response.status_code == 200:
            print("✅ Edge Config read successful")
            return True
        elif response.status_code == 404:
            print("ℹ️ Edge Config item not found (first run)")
            return True
        else:
            print(f"❌ Edge Config read failed: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def test_write():
    print("\n=== Edge Config Write Test ===")
    
    edge_db_url = os.environ.get('EDGE_DB')
    if not edge_db_url:
        return False
    
    try:
        # Parse URL
        if '?' in edge_db_url:
            base_url, params = edge_db_url.split('?', 1)
            edge_config_id = base_url.split('/')[-1]
            token_param = [p for p in params.split('&') if p.startswith('token=')]
            edge_config_token = token_param[0].split('=')[1] if token_param else None
        else:
            edge_config_id = edge_db_url.split('/')[-1]
            edge_config_token = None
        
        # Test write
        headers = {'Content-Type': 'application/json'}
        if edge_config_token:
            headers['Authorization'] = f'Bearer {edge_config_token}'
        
        write_url = f'https://api.vercel.com/v1/edge-config/{edge_config_id}/item'
        test_data = {
            'key': 'app_data',
            'value': {
                "chapters": [
                    {"id": 1, "name": "Test Chapter", "description": "Test description"}
                ],
                "questions": [],
                "user_answers": [],
                "sessions": []
            }
        }
        
        print(f"Write URL: {write_url}")
        print(f"Headers: {headers}")
        
        response = requests.patch(write_url, headers=headers, json=test_data)
        print(f"Response status: {response.status_code}")
        print(f"Response text: {response.text}")
        
        if response.status_code == 200:
            print("✅ Edge Config write successful")
            return True
        else:
            print(f"❌ Edge Config write failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

if __name__ == '__main__':
    test_edge_config()
    test_write()
