import time
import logging
import concurrent.futures
from chat_zai_client import ChatZaiClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_single_request(client, request_id, prompt):
    logging.info(f"🚀 [Req {request_id}] Sending request...")
    start_time = time.time()
    try:
        response = client.generate(prompt, max_tokens=100)
        duration = time.time() - start_time
        logging.info(f"✅ [Req {request_id}] Completed in {duration:.2f}s")
        logging.info(f"📝 [Req {request_id}] Response: {response[:50]}...")
        return True
    except Exception as e:
        duration = time.time() - start_time
        logging.error(f"❌ [Req {request_id}] Failed in {duration:.2f}s: {e}")
        return False

def main():
    logging.info("Testing parallel API requests to ChatZai...")
    
    # Initialize client
    client = ChatZaiClient(api_url="http://localhost:3001", timeout=120)
    
    # Check health
    if not client.health_check():
        logging.error("❌ API Server is not running at http://localhost:3001")
        return

    logging.info("✅ API Server is healthy")
    
    # Test 2 parallel requests
    prompts = [
        "Write a short sentence about coffee.",
        "Write a short sentence about tea."
    ]
    
    logging.info(f"⚡ Sending {len(prompts)} requests in parallel...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futures = []
        for i, prompt in enumerate(prompts):
            # Submit tasks with 1s delay
            if i > 0:
                logging.info("⏳ Waiting 1s before next request...")
                time.sleep(1)
            futures.append(executor.submit(test_single_request, client, i+1, prompt))
            
        # Wait for results
        concurrent.futures.wait(futures)
        
    logging.info("🏁 Test complete")

if __name__ == "__main__":
    main()
