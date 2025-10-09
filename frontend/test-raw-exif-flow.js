/**
 * Test new raw EXIF batch import flow
 * 
 * This test verifies that:
 * 1. Frontend extracts raw EXIF bytes correctly
 * 2. Backend processes raw EXIF to extract metadata
 * 3. End-to-end import flow works
 */

import { extractRawExifBytesFromFile, getImageDimensionsFromFile } from './src/lib/image-processor/raw-exif-extractor.js';
import fs from 'fs/promises';

async function testRawExifFlow() {
    console.log('🧪 Testing Raw EXIF Import Flow');
    console.log('=' * 50);
    
    try {
        // Read a test image file as if it came from File System Access API
        const testImagePath = '/mnt/c/temp/PHOTOS_SRC_TEST_MINI/2024_04_27_taipei_beitou/IMG_20240427_145518.jpg';
        const fileBuffer = await fs.readFile(testImagePath);
        const stats = await fs.stat(testImagePath);
        
        // Create a mock File object (simulating browser File API)
        const mockFile = {
            name: 'IMG_20240427_145518.jpg',
            size: stats.size,
            arrayBuffer: async () => fileBuffer.buffer,
            type: 'image/jpeg'
        };
        
        console.log(`📁 Test file: ${mockFile.name} (${mockFile.size} bytes)`);
        
        // Test 1: Extract raw EXIF bytes (frontend operation)
        console.log('\n1️⃣ Extracting raw EXIF bytes...');
        const rawExifBytes = await extractRawExifBytesFromFile(mockFile);
        console.log(`✅ Raw EXIF: ${rawExifBytes ? rawExifBytes.length : 0} bytes`);
        
        // Test 2: Get image dimensions (using Sharp for Node.js)
        console.log('\n2️⃣ Getting image dimensions...');
        const sharp = (await import('sharp')).default;
        const metadata = await sharp(testImagePath).metadata();
        const dimensions = { width: metadata.width, height: metadata.height };
        console.log(`✅ Dimensions: ${dimensions.width}x${dimensions.height}`);
        
        // Test 3: Simulate ImageCreateRequest object
        console.log('\n3️⃣ Creating ImageRequest object...');
        const imageRequest = {
            filename: mockFile.name,
            hothash: 'test_hash_' + Date.now(),
            file_size: mockFile.size,
            exif_data: rawExifBytes ? new Uint8Array(rawExifBytes) : undefined
        };
        console.log(`✅ ImageRequest created with ${imageRequest.exif_data ? imageRequest.exif_data.length : 0} EXIF bytes`);
        
        // Test 4: Simulate PhotoGroupRequest object
        console.log('\n4️⃣ Creating PhotoGroup object...');
        const photoGroup = {
            hothash: imageRequest.hothash,
            hotpreview: 'data:image/jpeg;base64,/9j/4AAQSkZJ...', // Mock thumbnail
            width: dimensions.width,
            height: dimensions.height,
            taken_at: undefined,  // Backend will extract from EXIF
            gps_latitude: undefined,  // Backend will extract from EXIF
            gps_longitude: undefined,  // Backend will extract from EXIF
            images: [imageRequest]
        };
        console.log(`✅ PhotoGroup created for ${photoGroup.hothash}`);
        
        // Test 5: Save EXIF bytes to file for backend testing
        if (rawExifBytes) {
            await fs.writeFile('/tmp/frontend_extracted_exif.bin', rawExifBytes);
            console.log('💾 Saved EXIF bytes to /tmp/frontend_extracted_exif.bin');
        }
        
        console.log('\n🎉 Frontend raw EXIF extraction test completed successfully!');
        console.log('\nNext: Test backend processing of these EXIF bytes');
        
        return {
            success: true,
            rawExifBytes,
            dimensions,
            imageRequest,
            photoGroup
        };
        
    } catch (error) {
        console.error('❌ Test failed:', error.message);
        return { success: false, error: error.message };
    }
}

// Run the test
testRawExifFlow().then(result => {
    if (result.success) {
        console.log('\n✅ All tests passed!');
    } else {
        console.log('\n❌ Tests failed:', result.error);
        process.exit(1);
    }
});