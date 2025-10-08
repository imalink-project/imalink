/**
 * Hash Generation Service
 * Provides consistent hash generation using backend authority
 */

/**
 * Frontend hotpreview specification - must match backend exactly
 */
export const HOTPREVIEW_SPEC = {
  width: 300,
  height: 300,
  format: 'JPEG',
  quality: 85,
  crop: 'center',
  colorSpace: 'sRGB'
} as const;

/**
 * Generate hotpreview according to specification
 * @param file - Image file to process
 * @returns Promise<string> - Base64 encoded hotpreview
 */
export async function generateHotpreview(file: File): Promise<string | null> {
  return new Promise((resolve) => {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const img = new Image();
    
    img.onload = () => {
      // Set canvas size according to spec
      canvas.width = HOTPREVIEW_SPEC.width;
      canvas.height = HOTPREVIEW_SPEC.height;
      
      // Calculate crop dimensions (center crop)
      const sourceAspect = img.width / img.height;
      const targetAspect = HOTPREVIEW_SPEC.width / HOTPREVIEW_SPEC.height;
      
      let sourceX = 0, sourceY = 0, sourceWidth = img.width, sourceHeight = img.height;
      
      if (sourceAspect > targetAspect) {
        // Source is wider - crop horizontally
        sourceWidth = img.height * targetAspect;
        sourceX = (img.width - sourceWidth) / 2;
      } else {
        // Source is taller - crop vertically  
        sourceHeight = img.width / targetAspect;
        sourceY = (img.height - sourceHeight) / 2;
      }
      
      // Draw cropped and scaled image
      ctx?.drawImage(
        img,
        sourceX, sourceY, sourceWidth, sourceHeight,
        0, 0, HOTPREVIEW_SPEC.width, HOTPREVIEW_SPEC.height
      );
      
      // Convert to base64 with specified quality
      const dataUrl = canvas.toDataURL('image/jpeg', HOTPREVIEW_SPEC.quality / 100);
      const base64 = dataUrl.split(',')[1];
      resolve(base64);
    };
    
    img.onerror = () => resolve(null);
    img.src = URL.createObjectURL(file);
  });
}

/**
 * Generate consistent hash using backend authority
 * @param filename - Image filename
 * @param fileSize - File size in bytes
 * @param width - Image width (optional)
 * @param height - Image height (optional)
 * @returns Promise<string> - Consistent hothash
 */
export async function generateConsistentHash(
  filename: string,
  fileSize: number,
  width?: number,
  height?: number
): Promise<string> {
  try {
    const params = new URLSearchParams({
      filename,
      file_size: fileSize.toString(),
      ...(width && { width: width.toString() }),
      ...(height && { height: height.toString() })
    });
    
    const response = await fetch(`http://localhost:8000/api/v1/test/generate-hash?${params}`, {
      method: 'POST'
    });
    
    if (!response.ok) {
      throw new Error(`Hash generation failed: ${response.status}`);
    }
    
    const result = await response.json();
    return result.hothash;
  } catch (error) {
    console.error('Failed to generate consistent hash:', error);
    // Fallback to simple hash if backend unavailable
    return generateFallbackHash(filename, fileSize, width, height);
  }
}

/**
 * Fallback hash generation (should match backend algorithm)
 * @param filename - Image filename  
 * @param fileSize - File size in bytes
 * @param width - Image width (optional)
 * @param height - Image height (optional)
 * @returns string - Fallback hash
 */
function generateFallbackHash(
  filename: string,
  fileSize: number,
  width?: number,
  height?: number
): string {
  // Normalize filename - same logic as backend
  const pathParts = filename.split(/[/\\]/);
  const baseName = pathParts[pathParts.length - 1];
  const dotIndex = baseName.lastIndexOf('.');
  const name = dotIndex > 0 ? baseName.substring(0, dotIndex).toLowerCase() : baseName.toLowerCase();
  const ext = dotIndex > 0 ? baseName.substring(dotIndex).toLowerCase() : '';
  const normalizedFilename = `${name}${ext}`;
  
  // Create hash input - same format as backend
  const hashInputParts = [normalizedFilename, fileSize.toString()];
  
  if (width && height) {
    hashInputParts.push(width.toString(), height.toString());
  }
  
  const hashInput = hashInputParts.join('|');
  
  // Simple hash function (crypto API would be better but this is fallback)
  let hash = 0;
  for (let i = 0; i < hashInput.length; i++) {
    const char = hashInput.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32-bit integer
  }
  
  // Convert to hex and pad to 32 characters
  return Math.abs(hash).toString(16).padStart(32, '0').substring(0, 32);
}

/**
 * Validate frontend synchronization with backend
 * @returns Promise<boolean> - True if frontend is properly synchronized
 */
export async function validateFrontendSync(): Promise<boolean> {
  try {
    // Get pilot data from backend
    const pilotResponse = await fetch('http://localhost:8000/api/v1/test/pilot-hash');
    if (!pilotResponse.ok) return false;
    
    const pilotData = await pilotResponse.json();
    const pilot = pilotData.pilot_image;
    
    // Generate hash using our function
    const frontendHash = await generateConsistentHash(
      pilot.filename,
      pilot.file_size,
      pilot.width,
      pilot.height
    );
    
    // Validate with backend
    const validateResponse = await fetch('http://localhost:8000/api/v1/test/validate-frontend', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        filename: pilot.filename,
        file_size: pilot.file_size,
        width: pilot.width,
        height: pilot.height,
        frontend_hash: frontendHash
      })
    });
    
    if (!validateResponse.ok) return false;
    
    const validation = await validateResponse.json();
    return validation.valid;
  } catch (error) {
    console.error('Frontend sync validation failed:', error);
    return false;
  }
}