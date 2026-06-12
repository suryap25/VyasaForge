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
        "action": action