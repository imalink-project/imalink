import { json } from '@sveltejs/kit';

export async function POST({ request }) {
    try {
        const { images, authorId } = await request.json();
        
        if (!images || !Array.isArray(images)) {
            return json({ error: 'Processed images array is required' }, { status: 400 });
        }

        // Call backend API to import to database
        const backendUrl = 'http://localhost:8000'; // Should be configurable
        
        const importPromises = images.map(async (image) => {
            try {
                const formData = new FormData();
                
                // Add image metadata
                formData.append('filename', image.filename);
                if (authorId) {
                    formData.append('author_id', authorId);
                }
                
                // Add EXIF data
                if (image.exif) {
                    Object.entries(image.exif).forEach(([key, value]) => {
                        if (value !== null && value !== undefined) {
                            formData.append(key, String(value));
                        }
                    });
                }
                
                // Add thumbnail if available
                if (image.thumbnail) {
                    formData.append('hotpreview', image.thumbnail);
                }
                
				const response = await fetch(`${backendUrl}/api/v1/images/`, {
					method: 'POST',
					body: formData
				});                if (response.ok) {
                    return { success: true, filename: image.filename };
                } else {
                    throw new Error(`HTTP ${response.status}`);
                }
            } catch (error) {
                return { 
                    success: false, 
                    filename: image.filename, 
                    error: error.message 
                };
            }
        });
        
        const results = await Promise.all(importPromises);
        const imported = results.filter(r => r.success);
        const failed = results.filter(r => !r.success);
        
        return json({
            success: true,
            imported,
            failed,
            skipped: [] // For now, no duplicate detection
        });
        
    } catch (error) {
        console.error('Import error:', error);
        return json({ 
            error: error.message || 'Failed to import images' 
        }, { status: 500 });
    }
}