import { error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';

const BACKEND_URL = 'http://localhost:8000';

export const GET: RequestHandler = async ({ params, fetch }) => {
	try {
		const { hothash } = params;
		
		// Forward request to backend
		const backendUrl = `${BACKEND_URL}/api/v1/photos/${hothash}/hotpreview`;
		const backendResponse = await fetch(backendUrl);
		
		if (!backendResponse.ok) {
			throw error(backendResponse.status, `Backend returned ${backendResponse.status}: ${backendResponse.statusText}`);
		}
		
		// Get the image data and content type
		const imageData = await backendResponse.arrayBuffer();
		const contentType = backendResponse.headers.get('content-type') || 'image/jpeg';
		
		// Return the image with proper headers
		return new Response(imageData, {
			status: 200,
			headers: {
				'Content-Type': contentType,
				'Cache-Control': 'public, max-age=3600', // Cache for 1 hour
			}
		});
	} catch (err) {
		console.error('Error proxying hotpreview:', err);
		throw error(500, 'Failed to fetch hotpreview');
	}
};