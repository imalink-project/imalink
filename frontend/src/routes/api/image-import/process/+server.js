import { json } from '@sveltejs/kit';
import { processImages } from '$lib/image-processor/index.js';

export async function POST({ request }) {
    try {
        const { images } = await request.json();
        
        if (!images || !Array.isArray(images)) {
            return json({ error: 'Images array is required' }, { status: 400 });
        }

        const results = await processImages(images);
        
        return json({
            success: true,
            ...results
        });
        
    } catch (error) {
        console.error('Process error:', error);
        return json({ 
            error: error.message || 'Failed to process images' 
        }, { status: 500 });
    }
}