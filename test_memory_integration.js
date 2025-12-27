// Simple test to verify memory API integration
const testMemoryAPI = async () => {
  try {
    // Test listing memories
    const listResponse = await fetch('/api/memory');
    const memories = await listResponse.json();
    console.log('Memory list test:', memories.length, 'memories found');

    // Test creating a memory
    const createResponse = await fetch('/api/memory', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        content: 'Test from frontend integration',
        category: 'fact'
      })
    });
    console.log('Create memory test:', createResponse.status);

    // Test search
    const searchResponse = await fetch('/api/memory/search?q=test');
    const searchResults = await searchResponse.json();
    console.log('Search test:', searchResults.length, 'results');

    return true;
  } catch (error) {
    console.error('Memory API test failed:', error);
    return false;
  }
};

// Run test if in browser environment
if (typeof window !== 'undefined') {
  testMemoryAPI();
}