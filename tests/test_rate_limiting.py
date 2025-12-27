"""Test Feature #97: Rate limiting prevents API abuse.

This test verifies that the rate limiting middleware properly prevents API abuse
by tracking requests and returning appropriate responses when limits are exceeded.
"""

import asyncio
import time
from httpx import AsyncClient, ASGITransport

from src.main import app


async def test_rate_limiting_prevents_api_abuse():
    """Test complete rate limiting workflow.

    Feature #97 Steps:
    1. Send many requests in quick succession
    2. Verify rate limit headers are present
    3. Exceed rate limit
    4. Verify 429 Too Many Requests response
    5. Wait for rate limit reset
    6. Verify requests succeed again
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        print("\n=== Step 1: Send many requests in quick succession ===")

        # Send requests rapidly to trigger rate limiting
        responses = []
        start_time = time.time()

        # Send more requests than the per-minute limit (60)
        for i in range(65):  # Exceed the 60 requests per minute limit
            response = await client.get("/health")  # Use health endpoint (should be skipped)
            responses.append(response)

        end_time = time.time()
        print(f"  ✓ Sent 65 requests in {end_time - start_time:.2f} seconds")

        # Since /health is in skip_paths, all should succeed
        success_count = sum(1 for r in responses if r.status_code == 200)
        print(f"  ✓ {success_count}/{len(responses)} requests succeeded")

        # Now test with a non-skipped endpoint
        print("\n=== Testing with non-skipped endpoint ===")

        # Send requests to trigger rate limiting
        limited_responses = []
        for i in range(70):  # Exceed the 60 requests per minute limit
            response = await client.get("/api/agent/models")  # Non-skipped endpoint
            limited_responses.append(response)

        # Count successful vs rate limited responses
        success_count = sum(1 for r in limited_responses if r.status_code == 200)
        rate_limited_count = sum(1 for r in limited_responses if r.status_code == 429)

        print(f"  ✓ {success_count} requests succeeded before rate limit")
        print(f"  ✓ {rate_limited_count} requests were rate limited")

        # At least some requests should be rate limited
        assert rate_limited_count > 0, "Expected some requests to be rate limited"

        print("\n=== Step 2: Verify rate limit headers are present ===")

        # Check that successful responses have rate limit headers
        successful_response = None
        for r in limited_responses:
            if r.status_code == 200 and "X-RateLimit-Limit-Minute" in r.headers:
                successful_response = r
                break

        if successful_response:
            headers = successful_response.headers
            required_headers = [
                "X-RateLimit-Limit-Minute",
                "X-RateLimit-Remaining-Minute",
                "X-RateLimit-Reset-Minute",
                "X-RateLimit-Limit-Hour",
                "X-RateLimit-Remaining-Hour",
                "X-RateLimit-Reset-Hour",
            ]

            for header in required_headers:
                assert header in headers, f"Missing header: {header}"
                print(f"  ✓ {header}: {headers[header]}")

        print("\n=== Step 3: Exceed rate limit ===")

        # Already done above - verify we got 429 responses
        assert rate_limited_count > 0, "Should have rate limited responses"

        print("\n=== Step 4: Verify 429 Too Many Requests response ===")

        # Find a rate limited response and verify its structure
        rate_limited_response = None
        for r in limited_responses:
            if r.status_code == 429:
                rate_limited_response = r
                break

        assert rate_limited_response is not None, "Should have found a 429 response"

        # Verify response content
        response_data = rate_limited_response.json()
        assert response_data["error"] == "Too Many Requests"
        assert "Rate limit exceeded" in response_data["message"]

        # Verify 429 response has rate limit headers
        headers = rate_limited_response.headers
        required_headers = [
            "X-RateLimit-Limit-Minute",
            "X-RateLimit-Remaining-Minute",
            "X-RateLimit-Reset-Minute",
            "X-RateLimit-Limit-Hour",
            "X-RateLimit-Remaining-Hour",
            "X-RateLimit-Reset-Hour",
            "X-RateLimit-Blocked-Until",
        ]

        for header in required_headers:
            assert header in headers, f"Missing header in 429 response: {header}"
            print(f"  ✓ {header}: {headers[header]}")

        print("\n=== Step 5: Wait for rate limit reset ===")

        # Get the blocked until time from the header
        blocked_until = int(headers["X-RateLimit-Blocked-Until"])
        current_time = time.time()
        wait_time = max(0, blocked_until - current_time + 1)

        if wait_time > 0:
            print(f"  ⏳ Waiting {wait_time:.1f} seconds for rate limit to reset...")
            await asyncio.sleep(wait_time)
        else:
            print(f"  ✅ Rate limit should already be reset (wait_time: {wait_time})")

        print("\n=== Step 6: Verify requests succeed again ===")

        # Send a few more requests after the wait
        post_wait_responses = []
        for i in range(5):
            response = await client.get("/api/agent/models")
            post_wait_responses.append(response)

        # Should have some successful responses now
        post_success_count = sum(1 for r in post_wait_responses if r.status_code == 200)
        print(f"  ✓ {post_success_count}/{len(post_wait_responses)} requests succeeded after reset")

        # Should have at least some successful responses
        assert post_success_count > 0, "Expected some requests to succeed after reset"

        print("\n" + "=" * 60)
        print("Feature #97 Test Summary:")
        print("=" * 60)
        print("✅ All 6 steps passed successfully!")
        print("✅ Rate limiting prevents API abuse")
        print("✅ Proper headers returned")
        print("✅ 429 responses with correct structure")
        print("✅ Rate limits reset after timeout")
        print("=" * 60)


async def test_rate_limiting_different_endpoints():
    """Test that rate limiting applies to different endpoints consistently."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        print("\n=== Testing rate limiting across different endpoints ===")

        # Send requests to different endpoints
        endpoints = ["/api/agent/models", "/api/agent/tools", "/api/conversations"]
        responses = []

        for endpoint in endpoints:
            for i in range(20):  # Send 20 requests to each endpoint
                response = await client.get(endpoint)
                responses.append((endpoint, response))

        # Count responses by status and endpoint
        endpoint_success = {}
        endpoint_limited = {}

        for endpoint, response in responses:
            if endpoint not in endpoint_success:
                endpoint_success[endpoint] = 0
                endpoint_limited[endpoint] = 0

            if response.status_code == 200:
                endpoint_success[endpoint] += 1
            elif response.status_code == 429:
                endpoint_limited[endpoint] += 1

        print("  ✓ Success counts by endpoint:")
        for endpoint, count in endpoint_success.items():
            print(f"    {endpoint}: {count}")

        print("  ✓ Rate limited counts by endpoint:")
        for endpoint, count in endpoint_limited.items():
            print(f"    {endpoint}: {count}")

        # Verify rate limiting is applied consistently
        total_success = sum(endpoint_success.values())
        total_limited = sum(endpoint_limited.values())

        print(f"  ✓ Total successful: {total_success}")
        print(f"  ✓ Total rate limited: {total_limited}")

        # Should have some rate limiting across endpoints
        assert total_limited > 0, "Expected some rate limiting across endpoints"


async def test_rate_limiting_skipped_paths():
    """Test that certain paths are skipped from rate limiting."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        print("\n=== Testing skipped paths ===")

        # Paths that should be skipped
        skipped_paths = ["/health", "/docs", "/openapi.json", "/redoc"]

        for path in skipped_paths:
            responses = []
            for i in range(100):  # Send many requests
                response = await client.get(path)
                responses.append(response)

            # All requests to skipped paths should succeed
            success_count = sum(1 for r in responses if r.status_code == 200)
            print(f"  ✓ {path}: {success_count}/{len(responses)} requests succeeded")

            # Should have no rate limiting on skipped paths
            rate_limited_count = sum(1 for r in responses if r.status_code == 429)
            assert rate_limited_count == 0, f"Unexpected rate limiting on skipped path: {path}"


if __name__ == "__main__":
    import sys
    import asyncio

    async def run_tests():
        await test_rate_limiting_prevents_api_abuse()
        await test_rate_limiting_different_endpoints()
        await test_rate_limiting_skipped_paths()

    asyncio.run(run_tests())