import { Client } from '@opensearch-project/opensearch';

import {
	OPENSEARCH_USERNAME,
	OPENSEARCH_PASSWORD,
	OPENSEARCH_INDEX,
	OPENSEARCH_NODE
} from '$env/static/private';

// // Middleware
// app.use(cors());
// app.use(express.json());

// OpenSearch client setup
const client = new Client({
	node: OPENSEARCH_NODE,
	auth: {
		username: OPENSEARCH_USERNAME,
		password: OPENSEARCH_PASSWORD
	}
});

export async function GET({ params }) {
	try {
		const response = await client.search({
			index: OPENSEARCH_INDEX,
			body: {
				query: {
					match_all: {}
				},
				size: params.size
			}
		});
		return new Response(JSON.stringify(response.body.hits.hits));
	} catch (error) {
		console.error('Error:', error);
		return new Response('Error', { status: 404 });
	}
}
