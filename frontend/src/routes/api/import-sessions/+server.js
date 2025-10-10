import { json } from '@sveltejs/kit';

const BACKEND_URL = 'http://localhost:8000';

/** @type {import('./$types').RequestHandler} */
export async function GET() {
	try {
		const response = await fetch(`${BACKEND_URL}/api/v1/import_sessions/`);
		
		if (!response.ok) {
			console.error('Backend response error:', response.status, response.statusText);
			return json({ error: 'Failed to fetch import sessions' }, { status: response.status });
		}
		
		const data = await response.json();
		return json(data);
	} catch (error) {
		console.error('Error fetching import sessions:', error);
		return json({ error: 'Failed to connect to backend' }, { status: 500 });
	}
}