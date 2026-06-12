# Chapter 9: Authorization Strategies and Access Control

## Learning Objectives

After completing this chapter, you will be able to:

- Distinguish between authentication and authorization, and explain why both are essential to application security
- Identify and evaluate different authorization models (RBAC, ABAC, PBAC) for your application architecture
- Design and implement role-based and attribute-based access control systems that scale with application complexity
- Recognize common authorization vulnerabilities including broken access control, privilege escalation, and insecure direct object references
- Apply authorization testing techniques to validate access control enforcement across your application
- Review authorization code and architecture for security weaknesses during code review and threat modeling
- Implement authorization patterns that balance security, performance, and maintainability

## Conceptual Foundation

Authorization is the process of determining what an authenticated user is allowed to do. While authentication answers the question "Who are you?", authorization answers "What are you allowed to access?" This distinction is critical: a perfectly implemented authentication system provides no security benefit if authorization decisions are flawed or missing.

Authorization operates at multiple layers in modern applications. At the network layer, firewalls and security groups control which systems can communicate. At the application layer, authorization determines which users can perform which actions on which resources. At the data layer, authorization controls which records a user can read, modify, or delete. Effective authorization requires consistent enforcement across all these layers.

### Core Authorization Concepts

**Subjects** are the entities requesting access—typically users, but also service accounts, API clients, or other applications. **Resources** are the objects being protected: API endpoints, database records, files, or features. **Actions** are the operations being performed: read, write, delete, execute, or custom operations. **Policies** are the rules that determine whether a subject can perform an action on a resource.

Authorization decisions depend on context. A user might be allowed to read their own profile but not others' profiles. A manager might approve expenses under $5,000 but require escalation for larger amounts. A document might be readable by anyone in the organization but editable only by its owner. This contextual nature of authorization makes it fundamentally more complex than authentication.

### Authorization Models

**Role-Based Access Control (RBAC)** assigns permissions to roles, then assigns roles to users. A user with the "Editor" role can perform all actions associated with that role. RBAC is simple to understand and implement, making it the most common authorization model in traditional applications. However, RBAC becomes unwieldy when permissions don't align neatly with roles or when fine-grained control is needed.

**Attribute-Based Access Control (ABAC)** makes authorization decisions based on attributes of the subject, resource, action, and environment. A policy might state: "Allow read access to documents where the document's classification is less than or equal to the user's clearance level AND the current time is during business hours AND the user's department matches the document's department." ABAC provides flexibility and fine-grained control but requires more sophisticated policy engines and careful policy design to avoid unintended access.

**Permission-Based Access Control (PBAC)** grants specific permissions directly to users or groups. Rather than assigning roles, you assign permissions like "can_edit_post_5" or "can_delete_user_account". PBAC offers granularity but scales poorly as the number of permissions grows.

Most modern applications use a hybrid approach: RBAC for coarse-grained access (who can access the admin panel), ABAC for fine-grained decisions (which records can this user modify), and PBAC for specific capabilities (can this user invite others to the organization).

## Architecture Perspective

Authorization architecture must address several concerns: where authorization decisions are made, how policies are stored and evaluated, how authorization state is communicated between services, and how authorization scales across distributed systems.

### Centralized vs. Distributed Authorization

In a **centralized authorization** architecture, a single service makes all authorization decisions. When a user requests access to a resource, the application queries the authorization service with details about the subject, resource, and action. The authorization service evaluates policies and returns a decision. This approach ensures consistent policy enforcement and simplifies policy management, but creates a potential bottleneck and single point of failure.

In a **distributed authorization** architecture, authorization decisions are made locally by each service. Each service maintains its own policies and makes decisions independently. This approach scales better and reduces latency but risks inconsistent policy enforcement if policies diverge across services.

Most production systems use a hybrid: a centralized policy store with distributed decision-making. Services cache authorization policies locally and make decisions without calling a central service on every request. Policies are synchronized periodically or through event streams. This approach balances consistency, performance, and scalability.

### Authorization in Microservices

Microservices architectures complicate authorization because requests flow through multiple services, each of which must enforce authorization. Consider an e-commerce system where a user requests their order history. The request flows through an API gateway, an order service, and a payment service. Each service must verify that the user is authorized to access the specific orders they're requesting.

A common pattern is to include authorization context in request headers or tokens. When a user authenticates, they receive a token (JWT, OAuth token, or session cookie) that includes their identity and roles. As the request flows through services, each service extracts this context and makes authorization decisions. This approach requires careful token design to include sufficient context without creating massive tokens, and careful validation to ensure tokens haven't been tampered with.

Another pattern is to use a sidecar or service mesh to enforce authorization policies. The service mesh intercepts requests and applies authorization rules before forwarding them to the application. This approach centralizes authorization logic outside the application code, but requires infrastructure investment and careful policy design.

### Policy Storage and Evaluation

Authorization policies must be stored in a way that supports efficient evaluation and easy updates. Common approaches include:

**Database-backed policies** store policies in a relational database. Policies are queried at decision time. This approach is flexible and supports complex queries but can be slow if policies are large or complex.

**In-memory policy engines** load policies into memory and evaluate them locally. Examples include Open Policy Agent (OPA) and Casbin. This approach is fast and doesn't require network calls but requires careful synchronization when policies change.

**Attribute stores** maintain a database of subject and resource attributes. Authorization decisions are made by querying these attributes. This approach supports ABAC well but requires maintaining accurate attribute data.

**Policy-as-code** approaches treat policies as code that's version-controlled, tested, and deployed like application code. This approach improves auditability and enables policy testing but requires developers to understand policy languages.

## AppSec Lens

From an application security perspective, authorization is one of the most frequently exploited attack surfaces. The OWASP Top 10 consistently ranks broken access control as the most common vulnerability. Authorization flaws are often easy to exploit—a simple URL change or parameter modification can grant unauthorized access—and the impact is severe: attackers can read sensitive data, modify records, or perform privileged actions.

### Common Authorization Vulnerabilities

**Broken Access Control** occurs when authorization checks are missing, incomplete, or bypassable. An application might check authorization on the web interface but not on the API. A user might be able to change a URL parameter from `/users/123/profile` to `/users/456/profile` and access another user's data. An application might check that a user is logged in but not verify they have permission to perform the requested action.

**Privilege Escalation** allows a user to gain higher privileges than intended. A user with "Editor" role might be able to modify their own role to "Admin". A user might exploit a race condition to perform an action before authorization is checked. A user might find an endpoint that only checks authentication, not authorization, and use it to perform privileged actions.

**Insecure Direct Object References (IDOR)** occur when an application uses user-supplied input to directly access objects without proper authorization checks. If an application uses sequential IDs for resources (invoice 1001, 1002, 1003), an attacker can enumerate and access all invoices by incrementing the ID. If an application uses predictable identifiers (username in URL), an attacker can guess other users' identifiers.

**Horizontal Privilege Escalation** allows a user to access resources belonging to other users at the same privilege level. A user can view other users' profiles, edit other users' posts, or access other users' data. This is distinct from vertical privilege escalation, which involves gaining higher privilege levels.

**Vertical Privilege Escalation** allows a user to gain higher privilege levels. A regular user might access admin functions, or a manager might access CEO-only reports. This often results from missing authorization checks on privileged endpoints.

**Authorization Bypass** occurs when authorization can be circumvented through technical means. An attacker might bypass authorization by:
- Removing authorization tokens from requests
- Modifying tokens to claim higher privileges
- Exploiting race conditions in authorization checks
- Using HTTP method overloading (POST instead of DELETE)
- Exploiting path traversal to access protected resources
- Manipulating request parameters to change authorization context

### Authorization in Different Application Types

**Web Applications** typically use session-based authorization. When a user logs in, the server creates a session and stores authorization information (roles, permissions) in the session. The session ID is sent to the client in a cookie. On subsequent requests, the client sends the session ID, and the server looks up the session to determine authorization. This approach is simple but requires careful session management to prevent session hijacking or fixation.

**Single-Page Applications (SPAs)** often use token-based authorization. When a user logs in, the server returns a token (typically JWT) that the client stores and includes in subsequent requests. The token contains claims about the user's identity and roles. This approach works well for SPAs because tokens can be sent in headers rather than cookies, avoiding CSRF vulnerabilities. However, tokens must be carefully validated and must not be stored in ways that expose them to XSS attacks.

**Mobile Applications** face unique authorization challenges. Mobile apps often operate offline, requiring local authorization decisions. Tokens must be securely stored on the device. Mobile apps are more vulnerable to reverse engineering, so authorization logic shouldn't rely on client-side checks alone. Server-side authorization enforcement is essential.

**APIs** require authorization on every request. APIs often use API keys, OAuth tokens, or mutual TLS for authorization. Authorization must be enforced consistently across all endpoints. API authorization is particularly important because APIs are often accessed by third-party applications or scripts, increasing the risk of misuse.

## Developer Lens

From a developer perspective, authorization requires careful implementation at multiple points in the application. Authorization must be enforced consistently, efficiently, and in a way that's easy to understand and maintain.

### Authorization Implementation Patterns

**Declarative Authorization** uses annotations or configuration to specify authorization requirements. A developer marks a method or endpoint with `@RequireRole("Admin")` or `@RequirePermission("edit_post")`. The framework automatically checks authorization before executing the method. This approach is clean and easy to understand but can miss edge cases where authorization depends on method parameters or business logic.

```java
@RestController
@RequestMapping("/api/posts")
public class PostController {
    
    @GetMapping("/{id}")
    @RequirePermission("read_post")
    public Post getPost(@PathVariable Long id) {
        return postService.getPost(id);
    }
    
    @PutMapping("/{id}")
    @RequirePermission("edit_post")
    public Post updatePost(@PathVariable Long id, @RequestBody PostUpdate update) {
        // Authorization check: is this user allowed to edit this specific post?
        Post post = postService.getPost(id);
        if (!authorizationService.canEdit(getCurrentUser(), post)) {
            throw new ForbiddenException("You cannot edit this post");
        }
        return postService.update(post, update);
    }
}
```

**Imperative Authorization** explicitly checks authorization in code. A developer calls `authorizationService.checkPermission(user, action, resource)` at the point where authorization is needed. This approach is more verbose but allows fine-grained control and makes authorization decisions explicit.

```python
def update_post(post_id, update_data):
    post = get_post(post_id)
    current_user = get_current_user()
    
    # Explicit authorization check
    if not authorization_service.can_edit(current_user, post):
        raise ForbiddenException("You cannot edit this post")
    
    # Additional context-specific checks
    if post.published and not current_user.has_permission("edit_published_posts"):
        raise ForbiddenException("You cannot edit published posts")
    
    return post_service.update(post, update_data)
```

**Attribute-Based Authorization** makes decisions based on attributes of the subject, resource, and action. A policy engine evaluates a policy like "allow if user.department == resource.department AND user.clearance >= resource.classification". This approach is flexible but requires careful policy design.

```python
def check_access(user, resource, action):
    policy = {
        "effect": "allow",
        "principal": {"department": user.department},
        "action": action,
        "resource": {"department": resource.department, "classification": {"<=": user.clearance}},
        "condition": {"time_of_day": "business_hours"}
    }
    return policy_engine.evaluate(policy, user, resource, action)
```

### Authorization Testing in Development

Developers should test authorization as thoroughly as they test functionality. Authorization tests should verify:

- Users without required roles cannot access protected resources
- Users with required roles can access protected resources
- Users can only access their own data, not others' data
- Privilege escalation is not possible
- Authorization is enforced on all endpoints and methods
- Authorization decisions are consistent across the application

```python
def test_user_cannot_edit_others_posts():
    user1 = create_user("user1")
    user2 = create_user("user2")
    post = create_post(author=user1)
    
    # User2 should not be able to edit user1's post
    with pytest.raises(ForbiddenException):
        with user2_context():
            update_post(post.id, {"title": "Hacked"})

def test_user_can_edit_own_posts():
    user = create_user("user1")
    post = create_post(author=user)
    
    # User should be able to edit their own post
    with user_context(user):
        updated = update_post(post.id, {"title": "Updated"})
        assert updated.title == "Updated"

def test_admin_can_edit_any_post():
    admin = create_user("admin", roles=["admin"])
    user = create_user("user1")
    post = create_post(author=user)
    
    # Admin should be able to edit any post
    with admin_context():
        updated = update_post(post.id, {"title": "Admin Edit"})
        assert updated.title == "Admin Edit"
```

### Common Developer Mistakes

**Checking authorization only on the client side** is a critical mistake. Client-side checks can be bypassed by modifying JavaScript, using browser developer tools, or making direct API calls. Authorization must always be enforced on the server.

**Assuming authentication implies authorization** is another common error. Just because a user is logged in doesn't mean they can perform any action. Every action must be explicitly authorized.

**Forgetting to check authorization on all endpoints** happens when developers add authorization to some endpoints but miss others. An application might check authorization on the web interface but not on the API, or on GET requests but not on POST requests.

**Using user-supplied input in authorization decisions without validation** can lead to authorization bypass. If an application uses a user-supplied role parameter to determine authorization, an attacker can modify the parameter to claim higher privileges.

**Implementing authorization inconsistently** across the application creates confusion and security gaps. Authorization should follow consistent patterns throughout the application.

## Pentest Lens

From a penetration testing perspective, authorization is a high-value target. Authorization flaws are common, often easy to exploit, and have significant impact. Effective authorization testing requires understanding the application's authorization model and systematically testing for weaknesses.

### Authorization Testing Methodology

**Reconnaissance** involves understanding the application's authorization model. What roles exist? What permissions does each role have? How are users assigned to roles? What resources are protected? This information can be gathered from documentation, user interfaces, API responses, and error messages.

**Baseline Testing** establishes what the application should do. For each role, document what resources and actions should be accessible. Create test accounts for each role and verify that the application behaves as expected.

**Deviation Testing** looks for cases where the application doesn't behave as expected. Try to:
- Access resources without authentication
- Access resources with a different user's credentials
- Modify authorization tokens or cookies
- Change URL parameters to access other users' resources
- Use HTTP method overloading (try DELETE when POST is expected)
- Access endpoints that should be protected but aren't
- Escalate privileges by modifying role claims in tokens
- Exploit race conditions in authorization checks

**Horizontal Privilege Escalation Testing** attempts to access resources belonging to other users at the same privilege level. For each resource type (posts, comments, profiles, etc.), attempt to access resources belonging to other users by:
- Incrementing or decrementing numeric IDs
- Guessing usernames or email addresses
- Modifying URL parameters
- Changing request parameters
- Exploiting predictable identifiers

**Vertical Privilege Escalation Testing** attempts to gain higher privilege levels. Try to:
- Access admin endpoints as a regular user
- Modify role claims in tokens
- Exploit race conditions to perform privileged actions before authorization is checked
- Find endpoints that check authentication but not authorization
- Exploit business logic flaws to gain higher privileges

### Authorization Testing Checklist

```
Authorization Testing Checklist

[ ] Identify all roles and permissions in the application
[ ] Create test accounts for each role
[ ] Document expected access for each role
[ ] Test that users without authentication cannot access protected resources
[ ] Test that users with required roles can access protected resources
[ ] Test that users without required roles cannot access protected resources
[ ] Test horizontal privilege escalation (accessing other users' resources)
    [ ] Try incrementing/decrementing numeric IDs
    [ ] Try guessing usernames or email addresses
    [ ] Try modifying URL parameters
    [ ] Try changing request parameters
[ ] Test vertical privilege escalation (gaining higher privileges)
    [ ] Try accessing admin endpoints
    [ ] Try modifying role claims in tokens
    [ ] Try exploiting race conditions
    [ ] Try finding endpoints that skip authorization
[ ] Test authorization on all HTTP methods (GET, POST, PUT, DELETE, PATCH)
[ ] Test authorization on all endpoints (web, API, mobile)
[ ] Test authorization with modified tokens or cookies
[ ] Test authorization with removed tokens or cookies
[ ] Test authorization with invalid tokens or cookies
[ ] Test authorization with expired tokens or cookies
[ ] Test authorization with tokens from other users
[ ] Test authorization with tokens from other applications
[ ] Test authorization bypass techniques
    [ ] Path traversal
    [ ] HTTP method overloading
    [ ] Parameter pollution
    [ ] Case sensitivity
    [ ] Encoding variations
[ ] Test authorization in error conditions
[ ] Test authorization with concurrent requests
[ ] Test authorization with large or malformed requests
[ ] Verify authorization is enforced consistently across the application
```

### Authorization Testing Tools

**Burp Suite** is the standard tool for web application security testing. Use Burp to:
- Intercept and modify requests to test authorization
- Automate authorization testing across multiple endpoints
- Identify authorization patterns and anomalies
- Test for IDOR vulnerabilities

**OWASP ZAP** is a free alternative to Burp Suite with similar capabilities.

**Custom scripts** can automate authorization testing. A script can:
- Create test accounts for each role
- Log in as each user
- Request each resource
- Verify that access is granted or denied as expected
- Report deviations

**API testing tools** like Postman or REST Client can be used to test authorization on APIs by sending requests with different authentication credentials and verifying responses.

## Common Findings

Authorization vulnerabilities are among the most common security findings in application assessments. Understanding common patterns helps both developers and testers identify and fix authorization issues.

### Finding: Insecure Direct Object References (IDOR)

**Description**: The application uses user-supplied input to directly access objects without proper authorization checks. A user can access resources belonging to other users by modifying request parameters.

**Example**: An e-commerce application uses sequential invoice IDs. A user can view their invoice at `/invoices/1001` and can change the URL to `/invoices/1002` to view another user's invoice.

**Root Cause**: The application checks that a user is authenticated but doesn't verify that the user is authorized to access the specific resource.

**Remediation**:
```python
def get_invoice(invoice_id):
    current_user = get_current_user()
    invoice = Invoice.query.get(invoice_id)
    
    if not invoice:
        raise NotFoundError("Invoice not found")
    
    # Check authorization: user must own the invoice
    if invoice.user_id != current_user.id:
        raise ForbiddenException("You cannot access this invoice")
    
    return invoice
```

### Finding: Missing Authorization on API Endpoints

**Description**: Authorization is enforced on the web interface but not on the API. A user can perform privileged actions by calling the API directly.

**Example**: An application has a web interface that checks authorization before allowing users to delete posts. However, the

## Secure Design Guidance

### Authorization Design Principles

**Principle of Least Privilege**: Grant users only the minimum permissions necessary to perform their job functions. A content editor should not have database administrator privileges. A customer support representative should not access financial records. Start with no permissions and add only what's required. Regularly audit permissions to remove those no longer needed.

**Fail Secure**: When authorization decisions cannot be made, deny access by default. If a policy engine is unavailable, the application should deny access rather than allow it. If a token cannot be validated, the request should be rejected. If authorization context is missing or ambiguous, deny access. This principle ensures that failures result in security rather than vulnerability.

**Separation of Duties**: Distribute authorization decisions across multiple people or systems to prevent any single person from gaining excessive power. Require approval from multiple administrators to grant high-privilege roles. Require different people to request, approve, and implement access changes. This principle prevents insider threats and reduces the impact of compromised accounts.

**Defense in Depth**: Enforce authorization at multiple layers. Implement authorization at the API gateway, in the application code, and at the database layer. Don't rely on a single authorization check. If one layer is bypassed, others remain in place. This principle ensures that authorization failures in one layer don't compromise the entire system.

**Explicit Over Implicit**: Make authorization decisions explicit and visible. Use clear, understandable policy language. Log authorization decisions. Avoid implicit assumptions about what users should be able to do. If a user should have access to a resource, explicitly grant that access rather than relying on default behavior or inheritance.

### Authorization Architecture Decisions

**Choose the Right Authorization Model**: Select an authorization model that matches your application's needs:
- Use **RBAC** for applications with well-defined roles and relatively static permissions. RBAC is simple to implement and understand, making it suitable for traditional applications with clear organizational hierarchies.
- Use **ABAC** for applications requiring fine-grained, context-dependent access control. ABAC is necessary when authorization depends on multiple factors (user attributes, resource attributes, time, location, etc.) that don't fit neatly into roles.
- Use **PBAC** for applications where permissions are highly granular and don't align with roles. PBAC is useful for systems where users need specific, ad-hoc permissions that don't fit into predefined roles.
- Use **hybrid approaches** combining RBAC for coarse-grained access and ABAC for fine-grained decisions. Most production systems benefit from this approach.

**Decide on Centralization**: Determine whether authorization decisions should be centralized or distributed:
- **Centralized authorization** is appropriate for applications where consistent policy enforcement is critical and performance requirements allow for centralized decision-making. Use centralized authorization when policies must be synchronized across multiple services or when audit requirements demand centralized logging.
- **Distributed authorization** is appropriate for high-performance systems where latency is critical and services can operate independently. Use distributed authorization when services have distinct authorization requirements or when network calls to a central service would create bottlenecks.
- **Hybrid approaches** with centralized policy storage and distributed decision-making offer the best balance. Store policies centrally, distribute them to services, and make decisions locally.

**Design Token and Context Propagation**: In distributed systems, decide how authorization context flows between services:
- **Token-based propagation** includes authorization context in tokens (JWT, OAuth tokens) that flow with requests. Tokens should include sufficient context for authorization decisions without becoming excessively large. Include user identity, roles, and relevant attributes. Sign tokens cryptographically to prevent tampering.
- **Header-based propagation** passes authorization context in request headers. This approach works well for service-to-service communication where headers can be added by proxies or service meshes.
- **Service mesh enforcement** uses a service mesh to enforce authorization policies without requiring application code changes. The mesh intercepts requests and applies policies before forwarding to services.

**Plan for Policy Updates**: Design how authorization policies will be updated without requiring application restarts:
- **Database-backed policies** allow policies to be updated immediately but require database queries for every decision.
- **Cached policies** with periodic synchronization balance performance and freshness. Services cache policies locally and refresh periodically or when notified of changes.
- **Event-driven updates** use event streams to notify services when policies change, enabling near-real-time updates without polling.

### Implementation Guidance

**Implement Authorization Consistently**: Establish authorization patterns and enforce them throughout the application:
- Create reusable authorization components (middleware, decorators, utility functions) that implement authorization consistently.
- Use the same authorization checks for all endpoints, whether web, API, or mobile.
- Apply authorization at the earliest point in request processing to fail fast.
- Log all authorization decisions for audit purposes.

**Validate Authorization Context**: Never trust authorization context provided by clients:
- Validate that tokens are properly signed and haven't been tampered with.
- Verify that token claims match server-side records (user still exists, roles are current).
- Check that tokens haven't expired.
- Validate that authorization context is complete and unambiguous.

**Handle Authorization Failures Gracefully**: Provide appropriate responses when authorization fails:
- Return 403 Forbidden when a user is authenticated but not authorized.
- Return 401 Unauthorized when a user is not authenticated.
- Don't reveal information about what the user would need to access the resource (this could help attackers understand the authorization model).
- Log authorization failures for security monitoring.

**Test Authorization Thoroughly**: Include authorization testing in your development process:
- Write unit tests for authorization logic.
- Write integration tests that verify authorization across multiple components.
- Test both positive cases (authorized users can access) and negative cases (unauthorized users cannot).
- Test edge cases (expired tokens, missing context, concurrent requests).
- Include authorization testing in security testing and penetration testing.

### Database-Level Authorization

**Implement Row-Level Security**: Use database features to enforce authorization at the data layer:
- PostgreSQL Row-Level Security (RLS) policies automatically filter rows based on the current user.
- SQL Server Row-Level Security provides similar functionality.
- These features ensure that even if application-level authorization is bypassed, database-level authorization prevents unauthorized data access.

**Example PostgreSQL RLS Policy**:
```sql
-- Create a policy that allows users to see only their own posts
CREATE POLICY user_posts_policy ON posts
    USING (author_id = current_user_id());

-- Enable RLS on the posts table
ALTER TABLE posts ENABLE ROW LEVEL SECURITY;

-- Now queries automatically filter to the current user's posts
SELECT * FROM posts;  -- Returns only current user's posts
```

**Use Database Views for Authorization**: Create database views that enforce authorization:
- A view can filter data based on the current user or role.
- Applications query the view instead of the base table, ensuring authorization is enforced.
- This approach provides defense in depth: if application-level authorization is bypassed, the view still filters data.

**Audit Database Access**: Log all database access for authorization violations:
- Enable database audit logging to track who accessed what data.
- Monitor for unusual access patterns that might indicate authorization bypass.
- Use audit logs to investigate security incidents.

---

## Interview Questions

### For Developers

1. **Describe the authorization model used in your current application. How are roles and permissions defined and assigned?**
   - *Evaluates*: Understanding of authorization architecture, ability to articulate authorization design decisions.
   - *Look for*: Clear explanation of roles, permissions, and assignment mechanisms. Understanding of whether the model is RBAC, ABAC, or hybrid.

2. **Walk me through how you would implement authorization for a feature that allows users to edit only their own posts. Where would you place authorization checks?**
   - *Evaluates*: Practical authorization implementation skills, understanding of where authorization should be enforced.
   - *Look for*: Mentions of application-level checks, database-level checks, API endpoint checks. Understanding that authorization must be enforced at multiple layers.

3. **How do you test authorization in your application? Can you describe a test case that verifies a user cannot access another user's data?**
   - *Evaluates*: Commitment to authorization testing, understanding of test design.
   - *Look for*: Specific test examples, mention of testing both positive and negative cases, understanding of edge cases.

4. **What authorization vulnerabilities have you encountered or fixed in your code? How did you identify and remediate them?**
   - *Evaluates*: Real-world experience with authorization issues, ability to identify and fix vulnerabilities.
   - *Look for*: Specific examples, understanding of root causes, description of remediation approach.

5. **How would you handle authorization in a microservices architecture where requests flow through multiple services?**
   - *Evaluates*: Understanding of distributed authorization, ability to design authorization for complex architectures.
   - *Look for*: Discussion of token propagation, service-to-service authorization, consistency across services.

6. **Describe a situation where you had to choose between RBAC and ABAC. What factors influenced your decision?**
   - *Evaluates*: Understanding of different authorization models, ability to make appropriate architectural decisions.
   - *Look for*: Consideration of application requirements, scalability, complexity, and maintenance.

7. **How do you ensure that authorization policies are kept in sync across multiple services or instances?**
   - *Evaluates*: Understanding of policy management and synchronization in distributed systems.
   - *Look for*: Discussion of caching strategies, event-driven updates, or centralized policy stores.

### For Security Professionals

1. **Walk me through your methodology for testing authorization in a web application. What are the key areas you focus on?**
   - *Evaluates*: Systematic approach to authorization testing, understanding of common vulnerabilities.
   - *Look for*: Mention of horizontal and vertical privilege escalation, IDOR testing, endpoint enumeration, role-based testing.

2. **Describe a time when you discovered an authorization vulnerability. How did you identify it, and what was the impact?**
   - *Evaluates*: Real-world experience identifying authorization flaws, understanding of impact assessment.
   - *Look for*: Specific examples, description of testing methodology, understanding of severity and business impact.

3. **How would you test authorization in an API-based application where the web interface has different authorization than the API?**
   - *Evaluates*: Understanding of authorization testing across different interfaces, ability to identify inconsistencies.
   - *Look for*: Discussion of API endpoint enumeration, testing with different authentication methods, comparing web and API authorization.

4. **What techniques would you use to test for horizontal privilege escalation in an application with user-generated content?**
   - *Evaluates*: Understanding of IDOR and horizontal privilege escalation testing techniques.
   - *Look for*: Discussion of ID enumeration, parameter manipulation, predictable identifier testing.

5. **How would you approach testing authorization in a single-page application (SPA) that uses JWT tokens?**
   - *Evaluates*: Understanding of token-based authorization, SPA-specific testing considerations.
   - *Look for*: Discussion of token validation, token storage, token manipulation, client-side vs. server-side authorization.

6. **Describe how you would test authorization in a system with complex role hierarchies and delegated permissions.**
   - *Evaluates*: Understanding of complex authorization scenarios, ability to test sophisticated authorization models.
   - *Look for*: Discussion of role inheritance, permission delegation, testing edge cases in complex hierarchies.

7. **How do you determine whether an authorization vulnerability is a true security issue or a false positive?**
   - *Evaluates*: Judgment and understanding of authorization requirements, ability to assess actual risk.
   - *Look for*: Discussion of business requirements, intended authorization model, impact assessment.

### For Architects and Leaders

1. **How would you design an authorization system for a large, distributed application with multiple teams and services?**
   - *Evaluates*: Ability to design scalable authorization architecture, understanding of distributed systems challenges.
   - *Look for*: Discussion of centralized vs. distributed authorization, policy management, consistency, performance.

2. **What authorization model would you recommend for an application that needs to support complex, context-dependent access control?**
   - *Evaluates*: Understanding of different authorization models and their trade-offs.
   - *Look for*: Consideration of ABAC, policy engines, implementation complexity, maintenance burden.

3. **How would you ensure that authorization is consistently enforced across an organization's applications and services?**
   - *Evaluates*: Understanding of organizational security governance, ability to establish standards.
   - *Look for*: Discussion of standards, code review processes, testing requirements, tooling.

4. **What metrics or indicators would you use to assess the maturity of an organization's authorization practices?**
   - *Evaluates*: Understanding of authorization best practices, ability to measure and improve security posture.
   - *Look for*: Discussion of testing coverage, vulnerability metrics, policy documentation, incident tracking.

5. **How would you approach migrating from a simple RBAC system to a more sophisticated ABAC system without disrupting operations?**
   - *Evaluates*: Understanding of change management, ability to plan complex security improvements.
   - *Look for*: Discussion of phased migration, testing strategy, rollback plans, stakeholder communication.

6. **What authorization-related security requirements would you include in your application development standards?**
   - *Evaluates*: Ability to establish security requirements, understanding of authorization best practices.
   - *Look for*: Requirements for authorization testing, code review, logging, documentation, incident response.

---

## Key Takeaways

**Authorization is distinct from authentication and equally critical to security.** Authentication verifies identity; authorization determines what authenticated users can do. Both are essential. A perfect authentication system provides no security benefit if authorization is flawed. Every application must implement authorization consistently across all layers.

**Authorization vulnerabilities are among the most common and impactful security issues.** Broken access control consistently ranks as the top vulnerability in security assessments. Authorization flaws are often easy to exploit—a simple URL change or parameter modification can grant unauthorized access. The impact is severe: attackers can read sensitive data, modify records, or perform privileged actions. Authorization testing must be thorough and systematic.

**Choose an authorization model that matches your application's requirements.** RBAC is simple and suitable for applications with well-defined roles. ABAC provides flexibility for complex, context-dependent access control. PBAC offers granularity for specific permissions. Most applications benefit from hybrid approaches combining multiple models. The choice should be driven by application requirements, not by what's easiest to implement.

**Implement authorization at multiple layers for defense in depth.** Authorization should be enforced at the API gateway, in application code, and at the database layer. Don't rely on a single authorization check. If one layer is bypassed, others remain in place. This principle ensures that authorization failures in one layer don't compromise the entire system.

**Fail secure: deny access by default when authorization cannot be determined.** If a policy engine is unavailable, deny access. If a token cannot be validated, reject the request. If authorization context is missing or ambiguous, deny access. This principle ensures that failures result in security rather than vulnerability.

**Never trust authorization context provided by clients.** Always validate tokens, verify claims, and check that authorization context matches server-side records. Don't assume that client-side authorization checks are sufficient. Server-side authorization enforcement is essential.

**Test authorization as thoroughly as you test functionality.** Include authorization testing in development, code review, and security testing. Test both positive cases (authorized users can access) and negative cases (unauthorized users cannot). Test edge cases and error conditions. Automate authorization testing to catch regressions.

**Log and monitor authorization decisions for security and compliance.** Log successful and failed authorization attempts. Monitor for patterns that might indicate authorization bypass attempts or privilege escalation. Use logs for incident investigation and compliance auditing.

**Authorization in distributed systems requires careful design of context propagation.** In microservices architectures, authorization context must flow between services. Use tokens, headers, or service mesh policies to propagate context. Ensure that authorization decisions are consistent across services. Plan for policy synchronization and updates.

**Regularly audit and review authorization policies and assignments.** Authorization requirements change as applications evolve and organizations grow. Regularly review who has what permissions and whether those permissions are still appropriate. Remove permissions that are no longer needed. Document authorization decisions and rationale.

**Authorization is a shared responsibility across development, security, and operations.** Developers must implement authorization correctly. Security professionals must test authorization thoroughly. Operations must monitor authorization and respond to incidents. Leadership must establish authorization standards and ensure compliance. Effective authorization requires collaboration across all these roles.

## Sketchnote Placeholder

[SKETCHNOTE DIAGRAM PLACEHOLDER]
