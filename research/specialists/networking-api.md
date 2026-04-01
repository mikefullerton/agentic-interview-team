# Networking & API Specialist

## Domain Coverage
REST conventions, HTTP semantics, offline-first, caching, retry/resilience, timeouts, pagination, real-time communication, error response format, rate limiting.

## Cookbook Sources
- `cookbook/guidelines/networking/` (10+ guidelines)
- `cookbook/compliance/access-patterns.md`

## Structured Questions

1. Tell me about your API — REST, GraphQL, gRPC? What's the URL structure? Walk me through a typical request-response.

2. Does your app need to work offline? How do you handle mutations while offline — queue, optimistic apply, or something else? What if a sync fails?

3. User has a slow connection. What requests timeout, and how long do you wait? Retry, or tell the user immediately?

4. Paginating a list — offset, cursor, or something else? If items are added while paging, what happens?

5. Describe what an error response looks like. Code, message, nested details? Can the client programmatically determine what went wrong?

6. Connection drops while waiting for a response that will never arrive. How long does the app wait? What does the UI show? What happens at timeout?

7. API returns 429 (rate limited). What does the server include? How does the client respond — retry, back off, or error?

8. Can you add logging/metrics to all outgoing API calls in one place, or is HTTP code scattered?

9. API returns a large collection (thousands/millions). How do clients request a subset?

10. A feature requires real-time updates — notifications, live feeds, collaborative edits. WebSocket, SSE, or polling? Reconnection strategy?

11. Long-running operation (report generation, bulk import). Can't wait 10 minutes. How do you design that endpoint? What status codes?

12. Caching API responses on client — how long? When do you invalidate? What headers control this?

13. 100 requests to fetch a user's data from different endpoints. Can you batch them? How?

14. If the backend API changes (field renamed, new required parameter), how does the client find out? API versioning?

15. Monitoring — how do you know if requests are failing? Track latency? Error rates? How quickly would you notice degradation?

## Exploratory Prompts

1. If API latency doubled overnight, what breaks first? What brittle assumption are you making about response times?

2. Why does your app need offline? What's the actual user need — eventual consistency, local-first, or something else?

3. If the server rate-limited to 1 request per 10 seconds, how would your app behave? What would you redesign?

4. If you had to move from REST to GraphQL or gRPC, what's easier and harder? What's deeply tied to REST?
