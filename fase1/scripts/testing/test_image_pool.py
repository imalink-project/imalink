#!/usr/bin/env python3
"""
Test script for Image Pool Service
Demonstrates all key functionality
"""
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from services.image_pool import ImagePoolService
from config import config

def test_pool_service():
    """Test the image pool service functionality"""
    
    print("🔧 Testing Image Pool Service")
    print(f"Pool directory: {config.IMAGE_POOL_DIRECTORY}")
    print("📂 Using consolidated data structure: C:/temp/imalink_data/")
    
    # Initialize service
    pool_service = ImagePoolService(config.IMAGE_POOL_DIRECTORY)
    
    # Test 1: Pool stats (should be empty initially)
    print("\n📊 Pool Statistics:")
    stats = pool_service.get_pool_stats()
    print(f"Total files: {stats['total_files']}")
    print(f"Total size: {stats['total_size_mb']:.2f} MB")
    print(f"Size distribution: {stats['size_distribution']}")
    
    # Test 2: Path generation
    print("\n🗂️  Path Generation Test:")
    test_hash = "abcd1234ef567890abcdef123456"
    for size in ["large", "medium", "small"]:
        pool_path = pool_service._get_pool_path(test_hash, size)
        full_path = pool_service.get_full_path(test_hash, size)
        exists = pool_service.exists(test_hash, size)
        
        print(f"{size:6}: {pool_path} (exists: {exists})")
    
    # Test 3: Anti-upscaling logic
    print("\n🛡️  Anti-upscaling Test:")
    test_cases = [
        ((3000, 2000), "Large original"),
        ((900, 600), "Medium original"),
        ((300, 200), "Small original")
    ]
    
    for original_size, description in test_cases:
        print(f"\n{description}: {original_size[0]}x{original_size[1]}")
        for size_name, max_size in pool_service.sizes.items():
            target = pool_service._calculate_target_size(original_size, max_size)
            reduction = (original_size[0] * original_size[1]) / (target[0] * target[1])
            print(f"  {size_name:6} -> {target[0]:4}x{target[1]:4} (reduction: {reduction:.1f}x)")
    
    # Test 4: Analysis function
    print("\n🔍 Analysis Test (simulated):")
    mock_analysis = {
        "original_size": (2400, 1600),
        "original_megapixels": 3.84,
        "size_analysis": {},
        "recommended_sizes": [],
        "skippable_sizes": []
    }
    
    for size_name, max_size in pool_service.sizes.items():
        target_size = pool_service._calculate_target_size((2400, 1600), max_size)
        needs_scaling = target_size != (2400, 1600)
        
        mock_analysis["size_analysis"][size_name] = {
            "max_size": max_size,
            "target_size": target_size,
            "needs_scaling": needs_scaling
        }
        
        if needs_scaling:
            mock_analysis["recommended_sizes"].append(size_name)
        else:
            mock_analysis["skippable_sizes"].append(size_name)
    
    print(f"Recommended sizes: {mock_analysis['recommended_sizes']}")
    print(f"Skippable sizes: {mock_analysis['skippable_sizes']}")
    
    print("\n✅ All tests completed!")
    
    # Test with actual image if one exists
    test_image_path = Path("../test_user_files")
    if test_image_path.exists():
        print(f"\n🖼️  Looking for test images in {test_image_path}...")
        
        for img_file in test_image_path.glob("*.jpg"):
            print(f"Found test image: {img_file}")
            
            try:
                analysis = pool_service.analyze_original_requirements(img_file)
                print(f"Original: {analysis['original_size']} ({analysis['original_megapixels']:.1f}MP)")
                print(f"Recommended: {analysis['recommended_sizes']}")
                print(f"Skippable: {analysis['skippable_sizes']}")
            except Exception as e:
                print(f"Analysis failed: {e}")
            
            break  # Test only first image
    
    return True

if __name__ == "__main__":
    try:
        # Ensure directories exist
        config.ensure_directories()
        
        # Run tests
        success = test_pool_service()
        
        if success:
            print("\n🎉 Image Pool Service test completed successfully!")
        else:
            print("\n❌ Image Pool Service test failed!")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)