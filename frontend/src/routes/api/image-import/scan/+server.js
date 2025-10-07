import { json } from '@sveltejs/kit';
import { scanForImages } from '$lib/image-processor/index.js';

export async function POST({ request }) {
    try {
        const { directory } = await request.json();
        
        if (!directory) {
            return json({ error: 'Directory path is required' }, { status: 400 });
        }

        const images = await scanForImages(directory);
        
        return json({
            success: true,
            images,
            count: images.length
        });
        
    } catch (error) {
        console.error('Scan error:', error);
        return json({ 
            error: error.message || 'Failed to scan directory' 
        }, { status: 500 });
    }
}