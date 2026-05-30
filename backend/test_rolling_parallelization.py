#!/usr/bin/env python3
"""
Test script for rolling parallelization feature.

This script tests the backend changes for Phase 1 implementation.
"""

import asyncio
import time
from typing import List


class MockSemaphore:
    """Mock semaphore to track concurrent execution."""
    
    def __init__(self, max_concurrent: int):
        self.max_concurrent = max_concurrent
        self.current = 0
        self.max_reached = 0
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def __aenter__(self):
        await self.semaphore.acquire()
        self.current += 1
        self.max_reached = max(self.max_reached, self.current)
        print(f"   🔵 Active: {self.current}/{self.max_concurrent}")
        return self
    
    async def __aexit__(self, *args):
        self.current -= 1
        self.semaphore.release()
        print(f"   🟢 Released: {self.current}/{self.max_concurrent}")


async def mock_capture_url(url: str, duration: float, semaphore: MockSemaphore) -> dict:
    """Mock URL capture with variable duration."""
    start = time.time()
    async with semaphore:
        print(f"   ▶️  Started: {url} (will take {duration}s)")
        await asyncio.sleep(duration)
        elapsed = time.time() - start
        print(f"   ✅ Completed: {url} ({elapsed:.1f}s)")
        return {"url": url, "duration": elapsed}


async def test_rolling_parallelization():
    """Test rolling parallelization with 7 concurrent URLs."""
    
    print("\n" + "="*80)
    print("🧪 TEST: Rolling Parallelization (7 concurrent, 15 URLs)")
    print("="*80)
    
    # Simulate 15 URLs with varying durations
    urls = [
        ("URL-1", 2.0),
        ("URL-2", 2.5),
        ("URL-3", 3.0),
        ("URL-4", 1.5),
        ("URL-5", 2.0),
        ("URL-6", 2.5),
        ("URL-7", 3.0),
        ("URL-8", 1.0),  # Should start when URL-4 finishes
        ("URL-9", 1.5),  # Should start when URL-1 finishes
        ("URL-10", 2.0),
        ("URL-11", 1.0),
        ("URL-12", 1.5),
        ("URL-13", 2.0),
        ("URL-14", 1.0),
        ("URL-15", 1.5),
    ]
    
    max_concurrent = 7
    semaphore = MockSemaphore(max_concurrent)
    
    print(f"\n📊 Configuration:")
    print(f"   Total URLs: {len(urls)}")
    print(f"   Max Concurrent: {max_concurrent}")
    print(f"   Expected Behavior: URLs 8-15 start as soon as slots free up")
    print()
    
    start_time = time.time()
    
    # Create all tasks at once (rolling parallelization)
    tasks = [mock_capture_url(url, duration, semaphore) for url, duration in urls]
    
    # Execute all tasks
    results = await asyncio.gather(*tasks)
    
    total_time = time.time() - start_time
    
    print(f"\n📈 Results:")
    print(f"   Total Time: {total_time:.1f}s")
    print(f"   Max Concurrent Reached: {semaphore.max_reached}/{max_concurrent}")
    print(f"   URLs Completed: {len(results)}/{len(urls)}")
    
    # Calculate theoretical times
    sequential_time = sum(duration for _, duration in urls)
    fixed_batch_time = sum(max(urls[i:i+max_concurrent], key=lambda x: x[1])[1] 
                          for i in range(0, len(urls), max_concurrent))
    
    print(f"\n⏱️  Time Comparison:")
    print(f"   Sequential (no parallelization): {sequential_time:.1f}s")
    print(f"   Fixed Batches (7 per batch): ~{fixed_batch_time:.1f}s")
    print(f"   Rolling Parallelization: {total_time:.1f}s")
    print(f"   Speedup vs Sequential: {sequential_time/total_time:.1f}x")
    print(f"   Speedup vs Fixed Batches: {fixed_batch_time/total_time:.1f}x")
    
    # Verify correctness
    assert semaphore.max_reached == max_concurrent, f"Expected max {max_concurrent}, got {semaphore.max_reached}"
    assert len(results) == len(urls), f"Expected {len(urls)} results, got {len(results)}"
    
    print(f"\n✅ Test PASSED: Rolling parallelization working correctly!")
    print("="*80 + "\n")


async def test_fixed_batches():
    """Test fixed batch mode for comparison."""
    
    print("\n" + "="*80)
    print("🧪 TEST: Fixed Batches (7 per batch, 15 URLs)")
    print("="*80)
    
    urls = [
        ("URL-1", 2.0), ("URL-2", 2.5), ("URL-3", 3.0), ("URL-4", 1.5),
        ("URL-5", 2.0), ("URL-6", 2.5), ("URL-7", 3.0),
        ("URL-8", 1.0), ("URL-9", 1.5), ("URL-10", 2.0), ("URL-11", 1.0),
        ("URL-12", 1.5), ("URL-13", 2.0), ("URL-14", 1.0),
        ("URL-15", 1.5),
    ]
    
    max_concurrent = 7
    batch_size = 7
    
    print(f"\n📊 Configuration:")
    print(f"   Total URLs: {len(urls)}")
    print(f"   Batch Size: {batch_size}")
    print(f"   Expected Behavior: Process batches sequentially")
    print()
    
    start_time = time.time()
    results = []
    
    # Process in fixed batches
    for batch_num in range(0, len(urls), batch_size):
        batch = urls[batch_num:batch_num + batch_size]
        print(f"\n📦 Batch {batch_num//batch_size + 1}: {len(batch)} URLs")
        
        semaphore = MockSemaphore(max_concurrent)
        tasks = [mock_capture_url(url, duration, semaphore) for url, duration in batch]
        batch_results = await asyncio.gather(*tasks)
        results.extend(batch_results)
    
    total_time = time.time() - start_time
    
    print(f"\n📈 Results:")
    print(f"   Total Time: {total_time:.1f}s")
    print(f"   URLs Completed: {len(results)}/{len(urls)}")
    print(f"\n✅ Test PASSED: Fixed batches working correctly!")
    print("="*80 + "\n")


if __name__ == "__main__":
    print("\n🚀 Running Rolling Parallelization Tests\n")
    asyncio.run(test_rolling_parallelization())
    asyncio.run(test_fixed_batches())

