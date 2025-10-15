# API Documentation - PakJobs Aggregator

REST API documentation for accessing job data programmatically.

## Base URL

**Local Development**: `http://localhost:5000`  
**Production**: `https://pakjobs-api.onrender.com`

## Authentication

Currently, the API is **public and does not require authentication**. Rate limiting is enforced:
- **Limit**: 1000 requests per hour per IP address
- **Headers**: Check `X-RateLimit-Limit` and `X-RateLimit-Remaining` in responses

## Endpoints

### Health Check

Check API and database status.

**Endpoint**: `GET /health`

**Response**:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

---

### Get All Jobs

Retrieve paginated list of active jobs.

**Endpoint**: `GET /api/v1/jobs`

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `page` | integer | No | 1 | Page number |
| `limit` | integer | No | 100 | Items per page (max 1000) |

**Example Request**:
```bash
curl "https://pakjobs-api.onrender.com/api/v1/jobs?page=1&limit=50"
```

**Response**:
```json
{
  "page": 1,
  "limit": 50,
  "total": 25000,
  "total_pages": 500,
  "jobs": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Senior Python Developer",
      "company": "Tech Solutions Ltd",
      "location": "Karachi, Sindh",
      "city": "Karachi",
      "country": "Pakistan",
      "salary_text": "PKR 150,000 - 200,000",
      "salary_min": 150000,
      "salary_max": 200000,
      "salary_currency": "PKR",
      "description": "We are looking for an experienced Python developer...",
      "requirements": "5+ years of Python experience...",
      "skills": ["Python", "Django", "PostgreSQL", "Docker"],
      "experience_level": "Senior Level",
      "experience_years": "5-7 years",
      "job_type": "Full-time",
      "is_remote": false,
      "is_hybrid": true,
      "is_onsite": false,
      "application_method": "email",
      "application_email": "hr@techsolutions.pk",
      "application_url": null,
      "posted_date": "2025-01-15",
      "source_url": "https://www.rozee.pk/job/12345",
      "site_source": "rozee",
      "is_active": true
    }
  ]
}
```

---

### Search Jobs

Search jobs by keywords, location, or site.

**Endpoint**: `GET /api/v1/jobs/search`

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `q` | string | No | Search query (title, description, company) |
| `city` | string | No | Filter by city |
| `site` | string | No | Filter by site source |
| `limit` | integer | No | Max results (default: 100) |

**Example Request**:
```bash
curl "https://pakjobs-api.onrender.com/api/v1/jobs/search?q=python&city=karachi&limit=20"
```

**Response**:
```json
{
  "total": 15,
  "jobs": [
    {
      "id": "...",
      "title": "Python Developer",
      "company": "ABC Corp",
      ...
    }
  ]
}
```

---

### Get Statistics

Retrieve overall statistics.

**Endpoint**: `GET /api/v1/stats`

**Example Request**:
```bash
curl "https://pakjobs-api.onrender.com/api/v1/stats"
```

**Response**:
```json
{
  "total_jobs": 25000,
  "total_companies": 3500,
  "by_site": {
    "rozee": 8500,
    "mustakbil": 6200,
    "indeed": 5100,
    "brightspyre": 2000,
    "bayt": 1500,
    "jobz": 800,
    "bayrozgar": 400,
    "jobsalert": 300,
    "pakpositions": 200
  }
}
```

---

## Response Formats

### Success Response

**HTTP Status**: 200 OK

```json
{
  "data": {...},
  ...
}
```

### Error Response

**HTTP Status**: 400, 404, 500, 503

```json
{
  "error": "Error description"
}
```

## Common HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad Request (invalid parameters) |
| 404 | Not Found |
| 429 | Rate Limit Exceeded |
| 500 | Internal Server Error |
| 503 | Service Unavailable (database down) |

## Rate Limiting

**Headers in Response**:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 995
X-RateLimit-Reset: 1642348800
```

**Rate Limit Exceeded Response**:
```json
{
  "error": "Rate limit exceeded. Try again later."
}
```

## Data Export

For bulk data access, use the export endpoints (requires web browser):

- **CSV**: `GET /export?format=csv`
- **JSON**: `GET /export?format=json`
- **Excel**: `GET /export?format=excel`

Max 10,000 records per export.

## Code Examples

### Python

```python
import requests

# Get jobs
response = requests.get('https://pakjobs-api.onrender.com/api/v1/jobs', params={
    'page': 1,
    'limit': 100
})

jobs = response.json()
print(f"Total jobs: {jobs['total']}")

for job in jobs['jobs']:
    print(f"{job['title']} at {job['company']}")
```

### JavaScript (Node.js)

```javascript
const axios = require('axios');

async function getJobs() {
  const response = await axios.get('https://pakjobs-api.onrender.com/api/v1/jobs', {
    params: { page: 1, limit: 50 }
  });
  
  console.log(`Total jobs: ${response.data.total}`);
  response.data.jobs.forEach(job => {
    console.log(`${job.title} at ${job.company}`);
  });
}

getJobs();
```

### cURL

```bash
# Search for Python jobs in Karachi
curl -X GET "https://pakjobs-api.onrender.com/api/v1/jobs/search?q=python&city=karachi" \
  -H "Accept: application/json"
```

### PHP

```php
<?php
$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, 'https://pakjobs-api.onrender.com/api/v1/jobs?page=1&limit=50');
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);

$response = curl_exec($ch);
$data = json_decode($response, true);

echo "Total jobs: " . $data['total'] . "\n";

foreach ($data['jobs'] as $job) {
    echo $job['title'] . " at " . $job['company'] . "\n";
}

curl_close($ch);
?>
```

## Webhook Support

Currently not available. Planned for Phase 2.

## Versioning

API version is included in the URL: `/api/v1/...`

Future versions will be released as `/api/v2/...` with backward compatibility maintained.

## Support

For API issues or questions:
- GitHub Issues: [Repository link]
- Email: admin@pakjobs.example.com

## Changelog

### v1.0.0 (2025-01-15)
- Initial API release
- Endpoints: /jobs, /jobs/search, /stats
- Rate limiting: 1000 req/hour
- Public access (no auth)

---

**Happy coding! 🚀**
