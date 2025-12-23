import asyncio
import aiohttp
import json
import time

BASE_URL = "http://localhost:8000"
NOTE_NAME = "concurrency-test"
CONCURRENT_REQUESTS = 10

async def get_note_info(session, note_name):
    async with session.post(f"{BASE_URL}/netcut/note/info/", json={"note_name": note_name}) as response:
        return await response.json()

async def save_note(session, note_name, content, token, note_id):
    payload = {
        "note_id": note_id,
        "note_name": note_name,
        "note_content": content,
        "note_token": token,
        "expire_time": 3600,
        "note_pwd": ""
    }
    async with session.post(f"{BASE_URL}/netcut/note/save/", json=payload) as response:
        return await response.json()

async def simulate_user(user_id, session):
    # Same Note Conflict Test
    # 1. Get initial state
    info = await get_note_info(session, NOTE_NAME)
    token = info['data']['note_token']
    current_content = info['data']['note_content']
    note_id = info['data']['note_id']
    
    # 2. Try to save new content
    new_content = f"{current_content}\nUser {user_id} was here."
    print(f"User {user_id} attempting to save SAME note...")
    
    result = await save_note(session, NOTE_NAME, new_content, token, note_id)
    
    if 'status' not in result:
        print(f"❌ User {user_id} received unexpected response: {result}")
        return False

    if result['status'] == 1:
        print(f"✅ User {user_id} saved successfully.")
        return True
    else:
        print(f"❌ User {user_id} failed to save: {result.get('error')}")
        return False

async def simulate_independent_user(user_id, session):
    # Unique Note Independence Test
    my_note = f"note-user-{user_id}"
    
    # 1. Get initial state (Creates the note)
    info = await get_note_info(session, my_note)
    token = info['data']['note_token']
    note_id = info['data']['note_id']
    
    # 2. Save content
    new_content = f"Independent content for {user_id}"
    print(f"User {user_id} attempting to save UNIQUE note {my_note}...")
    
    result = await save_note(session, my_note, new_content, token, note_id)
    
    if result.get('status') == 1:
        print(f"✅ User {user_id} saved independent note successfully.")
        return True
    else:
        print(f"❌ User {user_id} failed to save independent note: {result.get('error')}")
        return False

async def main():
    async with aiohttp.ClientSession() as session:
        print("=== Test 1: Conflict Scenario (Same Note) ===")
        # Initialize the shared note
        print("Initializing shared note...")
        info = await get_note_info(session, NOTE_NAME)
        initial_token = info['data']['note_token']
        initial_id = info['data']['note_id']
        await save_note(session, NOTE_NAME, "Initial Content", initial_token, initial_id)
        
        # Run concurrent users on same note
        print(f"Starting {CONCURRENT_REQUESTS} concurrent requests on SAME note...")
        tasks = [simulate_user(i, session) for i in range(CONCURRENT_REQUESTS)]
        
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        success_count = sum(1 for r in results if r)
        fail_count = CONCURRENT_REQUESTS - success_count
        
        print("\n--- Conflict Test Results ---")
        print(f"Total Requests: {CONCURRENT_REQUESTS}")
        print(f"Successful Saves: {success_count} (Expected low, ideally 1)")
        print(f"Failed Saves: {fail_count} (Expected high)")
        print(f"Time Taken: {end_time - start_time:.2f}s")
        print("\n" + "="*30 + "\n")

        print("=== Test 2: Independence Scenario (Different Notes) ===")
        print(f"Starting {CONCURRENT_REQUESTS} concurrent requests on DIFFERENT notes...")
        tasks_indep = [simulate_independent_user(i, session) for i in range(CONCURRENT_REQUESTS)]
        
        start_time = time.time()
        results_indep = await asyncio.gather(*tasks_indep)
        end_time = time.time()
        
        success_indep = sum(1 for r in results_indep if r)
        fail_indep = CONCURRENT_REQUESTS - success_indep
        
        print("\n--- Independence Test Results ---")
        print(f"Total Requests: {CONCURRENT_REQUESTS}")
        print(f"Successful Saves: {success_indep} (Expected {CONCURRENT_REQUESTS})")
        print(f"Failed Saves: {fail_indep} (Expected 0)")
        print(f"Time Taken: {end_time - start_time:.2f}s")

if __name__ == "__main__":
    asyncio.run(main())
