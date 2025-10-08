/**
 * Test script for validating hash generation consistency
 */

// Test pilot data
const PILOT_TEST = {
  filename: 'test_image.jpg',
  file_size: 2458762,
  width: 1920,
  height: 1080
};

console.log('🧪 Testing hash generation consistency...');

// Test the API endpoints
async function testHashGeneration() {
  try {
    // 1. Get pilot hash from backend
    console.log('📡 Getting pilot hash from backend...');
    const pilotResponse = await fetch('http://localhost:8000/api/v1/test/pilot-hash');
    const pilotData = await pilotResponse.json();
    console.log('✅ Pilot data:', pilotData);
    
    // 2. Generate hash for test data
    console.log('🔍 Generating hash for test data...');
    const params = new URLSearchParams({
      filename: PILOT_TEST.filename,
      file_size: PILOT_TEST.file_size.toString(),
      width: PILOT_TEST.width.toString(),
      height: PILOT_TEST.height.toString()
    });
    
    const hashResponse = await fetch(`http://localhost:8000/api/v1/test/generate-hash?${params}`, {
      method: 'POST'
    });
    const hashData = await hashResponse.json();
    console.log('✅ Generated hash:', hashData);
    
    // 3. Validate consistency by generating same hash again
    console.log('🔄 Validating consistency...');
    const hash2Response = await fetch(`http://localhost:8000/api/v1/test/generate-hash?${params}`, {
      method: 'POST'
    });
    const hash2Data = await hash2Response.json();
    
    if (hashData.hothash === hash2Data.hothash) {
      console.log('✅ Hash generation is consistent!');
      console.log(`   Hash: ${hashData.hothash}`);
    } else {
      console.log('❌ Hash generation is inconsistent!');
      console.log(`   First:  ${hashData.hothash}`);
      console.log(`   Second: ${hash2Data.hothash}`);
    }
    
    // 4. Test validation endpoint
    console.log('🔍 Testing validation endpoint...');
    const validateResponse = await fetch('http://localhost:8000/api/v1/test/validate-frontend', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        filename: PILOT_TEST.filename,
        file_size: PILOT_TEST.file_size,
        width: PILOT_TEST.width,
        height: PILOT_TEST.height,
        frontend_hash: hashData.hothash
      })
    });
    const validateData = await validateResponse.json();
    console.log('✅ Validation result:', validateData);
    
  } catch (error) {
    console.error('❌ Test failed:', error);
  }
}

// Run the test if in browser environment
if (typeof window !== 'undefined') {
  testHashGeneration();
} else {
  console.log('ℹ️  Run this in browser console when server is running');
}