# ITVedas API Documentation

## Overview

ITVedas provides REST API endpoints for accessing career guidance and subscribing to content. All endpoints require proper origin validation for security.

---

## Endpoints

### POST /api/subscribe
Subscribe email address to ITVedas newsletter and updates.

**URL**: `/api/subscribe`  
**Method**: `POST`  
**Content-Type**: `application/json`

#### Request Body
```json
{
  "email": "user@example.com",
  "timestamp": "2026-07-17T10:30:00Z"
}
```

**Fields:**
- `email` (required, string): Valid email address
- `timestamp` (optional, ISO-8601): Subscription timestamp

#### Validation Rules
- Email must contain `@` symbol
- Email format: `user@domain.extension`
- Maximum payload: 6000 characters total
- Duplicate emails rejected

#### Response - Success (200)
```json
{
  "success": true,
  "message": "Successfully subscribed",
  "count": 1234
}
```

#### Response - Error (400, 500)
```json
{
  "success": false,
  "message": "Unable to process subscription. Please try again later."
}
```

**Error Codes:**
- `400` - Invalid JSON or missing required fields
- `405` - Only POST method allowed
- `500` - Server processing error

#### Security
- Origin validation (CORS)
- No error details exposed to client
- Email validation prevents injection
- Duplicate subscription prevention

---

### POST /api/career-advice
Get personalized IT career path recommendations based on quiz answers.

**URL**: `/api/career-advice`  
**Method**: `POST`  
**Content-Type**: `application/json`

#### Request Body
```json
{
  "answers": [
    {
      "question": "What interests you most?",
      "answer": "Building infrastructure"
    },
    {
      "question": "Preferred work environment?",
      "answer": "Collaborative team"
    }
  ]
}
```

**Fields:**
- `answers` (required, array): Quiz responses
  - `question` (string): Question text
  - `answer` (string): User's answer

#### Validation Rules
- `answers` array required, minimum 1 item
- Total character limit: 6000 characters
- Valid API key required (server-side)

#### Valid Career Paths
- `networking` - Networking & Infrastructure
- `cloud` - Cloud Computing
- `security` - Cybersecurity
- `devops` - DevOps & Automation
- `databases` - Databases & Data
- `linux` - Linux & Systems
- `hardware` - Hardware & Infrastructure
- `compliance` - IT Compliance & Risk

#### Response - Success (200)
```json
{
  "chapter": "cloud",
  "chapter_label": "Cloud Computing",
  "explanation": "Based on your interest in scalable infrastructure...",
  "next_steps": [
    "Start with AWS fundamentals",
    "Learn about cloud architectures",
    "Practice with cloud deployment"
  ]
}
```

#### Response - Error (400, 403, 500, 502)
```json
{
  "error": "Analysis service error"
}
```

**Error Codes:**
- `400` - Invalid JSON or validation error
- `403` - Origin not allowed (CORS violation)
- `500` - Server error
- `502` - Claude API service error

#### Security
- Origin validation (whitelisted domains + localhost dev)
- API key required (server-side environment variable)
- Input payload size limit (6000 chars)
- Generic error messages (no internal details exposed)

#### Allowed Origins
- `https://itvedas.com`
- `https://www.itvedas.com`
- `http://localhost:3000` (development)
- `http://localhost:8080` (development)
- `http://127.0.0.1:3000` (development)
- `http://127.0.0.1:8080` (development)

---

## Rate Limiting

Currently no rate limiting implemented. For production deployment, consider:
- Per-IP rate limits
- Per-origin rate limits
- Exponential backoff for retries

---

## CORS Headers

All endpoints return CORS headers:
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, OPTIONS
Access-Control-Allow-Headers: Content-Type
```

For production, consider restricting `Access-Control-Allow-Origin` to known domains only.

---

## Security Headers

All responses include security headers:
```
Content-Security-Policy: [policy]
Strict-Transport-Security: max-age=31536000
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
```

---

## Environment Variables

### Required
- `ANTHROPIC_API_KEY` - Claude API key for career advice generation

### Optional
- `DEBUG` - Enable debug logging (development only)

---

## Examples

### Subscribe with cURL
```bash
curl -X POST https://itvedas.com/api/subscribe \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com"
  }'
```

### Career Advice with cURL
```bash
curl -X POST https://itvedas.com/api/career-advice \
  -H "Content-Type: application/json" \
  -d '{
    "answers": [
      {"question": "Interest?", "answer": "Cloud platforms"},
      {"question": "Experience?", "answer": "5 years IT"}
    ]
  }'
```

### With JavaScript/Fetch
```javascript
const response = await fetch('/api/subscribe', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com'
  })
});

const data = await response.json();
if (data.success) {
  console.log('Subscribed!');
} else {
  console.error('Subscription failed');
}
```

---

## Troubleshooting

### CORS Error
- Ensure origin header matches allowed origins
- Check Origin header in request
- Verify domain is whitelisted

### Invalid Email Error
- Email must contain `@`
- Email must have domain extension (e.g., `.com`)
- Check for spaces or special characters

### Payload Too Large
- Reduce answer text length
- Limit to 6000 total characters across all answers

### API Service Error (502)
- Claude API may be temporarily unavailable
- Retry with exponential backoff
- Check API key configuration

---

## Changelog

### Version 1.0 (2026-07-17)
- Initial API documentation
- Subscribe endpoint documentation
- Career advice endpoint documentation
- Security headers documentation
- Origin validation documentation

---

**Last Updated**: 2026-07-17  
**API Version**: 1.0  
**Status**: Production Ready
