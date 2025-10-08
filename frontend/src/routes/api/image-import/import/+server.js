import { json } from '@sveltejs/kit';

export async function POST({ request }) {
    try {
        const { images, authorId } = await request.json();
        
        if (!images || !Array.isArray(images)) {
            return json({ error: 'Processed images array is required' }, { status: 400 });
        }

        // Convert processed images to PhotoGroup format for batch API
        const photoGroups = images.map(image => {
            // Generate simple hothash
            const hothash = btoa(`${image.filename}-${Date.now()}`).substring(0, 32).replace(/[+/=]/g, '');
            
            return {
                hothash: hothash,
                hotpreview: image.thumbnail || null,
                width: image.width || null,
                height: image.height || null,
                taken_at: image.taken_date ? new Date(image.taken_date).toISOString() : null,
                gps_latitude: image.exif?.gps_latitude || null,
                gps_longitude: image.exif?.gps_longitude || null,
                title: null,
                description: null,
                tags: null,
                rating: 0,
                user_rotation: 0,
                import_session_id: null,
                images: [{
                    filename: image.filename,
                    hothash: hothash,
                    file_size: image.file_size || null,
                    exif_data: image.exif ? new TextEncoder().encode(JSON.stringify(image.exif)) : null,
                    import_session_id: null
                }]
            };
        });

        // Use new Photos batch API
        const backendUrl = 'http://localhost:8000';
        const batchRequest = {
            photo_groups: photoGroups,
            author_id: authorId || null
        };

        const response = await fetch(`${backendUrl}/api/v1/photos/batch`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(batchRequest)
        });

        if (!response.ok) {
            const errorData = await response.text();
            throw new Error(`Batch API failed: ${response.status} - ${errorData}`);
        }

        const batchResult = await response.json();
        
        // Convert batch result to expected format
        const imported = batchResult.results
            .filter(r => r.success)
            .map(r => ({ success: true, filename: r.photo?.files?.[0]?.filename || r.hothash }));
            
        const failed = batchResult.results
            .filter(r => !r.success)
            .map(r => ({ success: false, filename: r.hothash, error: r.error }));
        
        return json({
            success: batchResult.success,
            imported,
            failed,
            skipped: [],
            batch_stats: {
                photos_created: batchResult.photos_created,
                photos_failed: batchResult.photos_failed,
                processing_time: batchResult.processing_time_seconds
            }
        });
        
    } catch (error) {
        console.error('Import error:', error);
        return json({ 
            error: error.message || 'Failed to import images' 
        }, { status: 500 });
    }
}