import { json } from '@sveltejs/kit';

const BACKEND_URL = 'http://localhost:8000';

/** @type {import('./$types').RequestHandler} */
export async function GET({ params, url }) {
	try {
		const { year } = params;
		const searchParams = url.searchParams.toString();
		const backendUrl = `${BACKEND_URL}/api/v1/timeline/years/${year}/months${searchParams ? `?${searchParams}` : ''}`;
		
		const response = await fetch(backendUrl);
		
		if (!response.ok) {
			console.error('Backend response error:', response.status, response.statusText);
			return json({ error: 'Failed to fetch timeline months' }, { status: response.status });
		}
		
		const data = await response.json();
		return json(data);
	} catch (error) {
		console.error('Error fetching timeline months:', error);
		return json({ error: 'Failed to connect to timeline backend' }, { status: 500 });
	}
}