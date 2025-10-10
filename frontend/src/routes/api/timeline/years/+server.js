import { json } from '@sveltejs/kit';

const BACKEND_URL = 'http://localhost:8000';

/** @type {import('./$types').RequestHandler} */
export async function GET({ url }) {
	try {
		// Forward all query parameters to backend
		const searchParams = url.searchParams.toString();
		const backendUrl = `${BACKEND_URL}/api/v1/timeline/years${searchParams ? `?${searchParams}` : ''}`;
		
		const response = await fetch(backendUrl);
		
		if (!response.ok) {
			console.error('Backend response error:', response.status, response.statusText);
			return json({ error: 'Failed to fetch timeline years' }, { status: response.status });
		}
		
		const data = await response.json();
		return json(data);
	} catch (error) {
		console.error('Error fetching timeline years:', error);
		return json({ error: 'Failed to connect to timeline backend' }, { status: 500 });
	}
}