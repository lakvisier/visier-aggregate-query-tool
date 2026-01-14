Here’s how “exceptional access” for Visier APIs via Support generally works, and what you should do when you need it.

From the internal SOP “Partner User Management and Exceptional Access”  
(https://visiercorp.atlassian.net/wiki/spaces/PSEAP/pages/3795189763/SOP+Partner+User+Management+and+Exceptional+Access):

### 1. When is “exceptional access” appropriate?

Exceptional access is meant for rare cases where Support (or an internal team) must temporarily perform actions that are normally restricted to:

- Tenant / user management
- User provisioning or modification that a partner/customer cannot do themselves
- Other highly-privileged API actions

It should only be used when:

- The partner/customer cannot reasonably perform the needed action themselves, and  
- The action is time‑bound and clearly justified.

### 2. Required contents of the request (what Support / approvers expect)

When you ask Support (or create a ticket) for exceptional access, you must include:

1. **Why exceptional access is needed**
   - Clear business reason or incident description.
   - Why normal processes / standard access are insufficient.

2. **What type of users are affected**
   - For example: “Partner admin users in tenant X,” “Customer end users in tenant Y,” “Support-only service account,” etc.

3. **Why the partner/customer cannot perform the action themselves**
   - E.g., “No admin user with correct profile yet,” “Self‑service flow blocked by defect,” “Requires Visier‑only API endpoint,” etc.

4. **Duration of access**
   - Very specific and short: e.g. “24 hours,” “48 hours,” “until yyyy‑mm‑dd hh:mm UTC, max 7 days.”
   - SOP calls out “absolute minimum time required, maximum one week.”

5. **Exact scope of access**
   - Which tenant(s)
   - Which profile(s) / roles
   - Which API or product area (e.g., user management, tenant management, Smart Compensation, etc.)

Support will use this to decide:

- Is exceptional access warranted?  
- What exact permissions to grant?  
- How long before access must be revoked?

### 3. Process overview

Per the SOP section 5.2 (Exceptional Access Request Process):

1. **Create a formal ticket**
   - Typically via your standard channel (e.g., ServiceNow or your agreed customer support portal).
   - One ticket per distinct request/scope/time window.

2. **Clearly describe justification in the ticket**
   - Include all points from section 2 (why needed, affected users, why customer/partner can’t do this, duration, scope).

3. **Approval**
   - The ticket must be approved by the defined authority (manager / designated approver for exceptional access).
   - Support should not self‑approve and execute without that sign‑off.

4. **Grant access for minimal time**
   - Access is provisioned only for the requested time window and exact scope.

5. **Revocation**
   - Once the work is complete, or the duration expires, exceptional access must be revoked immediately.

### 4. If your request is specifically about API usage

If you’re asking Support for exceptional API‑level access (for example, to manage external clients, tenants, or users programmatically):

- Reference the relevant API context in your ticket:
  - e.g. “Need temporary ability to call Visier API endpoints for tenant management / user provisioning on behalf of customer X.”
- Clarify:
  - Which API operations you need run (e.g., create tenant, modify modules, enable/disable tenant, manage users).
  - Whether Support is expected to run the API calls on your behalf or only to temporarily elevate your account/API user.

You can also reference the onboarding / API guides if you’re working in a partner context, e.g.:  
- Embedded Partners – External Client Onboarding Process Using the Visier API:  
  https://visiercorp.atlassian.net/wiki/pages/viewpageattachments.action?pageId=528351420&preview=%2F528351420%2F1947140168%2FEP+External+Client+Onboarding+Process+Using+the+Visier+API_en.pdf

### 5. A template you can reuse in your support ticket

You can paste/adapt this into your support case or internal ticket:

> **Subject:** Exceptional access request for Visier API – [tenant / customer name]
>
> **Why is exceptional access needed?**  
> [Short description of incident / project and why normal permissions or self‑service are insufficient.]
>
> **What type of users are affected?**  
> [e.g., Partner admin users; Customer end users in tenant X; Support service account; etc.]
>
> **Why can’t the partner/customer do this themselves?**  
> [e.g., no admin with required profile, blocked by defect, operation only available to Visier internal roles, etc.]
>
> **Scope of access requested:**  
> - Tenants: [list all]  
> - Profiles / roles / permissions: [list exact profiles or permissions required]  
> - Operations / APIs: [list specific tasks or endpoints, e.g., “create tenant, adjust modules, reset user access,” etc.]
>
> **Duration:**  
> [e.g., “From approval until yyyy‑mm‑dd hh:mm UTC, not to exceed 72 hours.”]
>
> **Post‑task actions:**  
> - Confirm once task is completed so all exceptional access can be revoked.  
> - Request verification/logs if required by audit.

If you tell me:

- Whether you are the partner, customer, or internal Visier staff, and  
- What concrete thing you need to do via the API that you can’t do with current permissions,

I can draft a fully‑filled version of this request that you can drop straight into your support channel or internal system.[1]

Sources:

1. https://visiercorp.atlassian.net/wiki/spaces/PSEAP/pages/3795189763/SOP+Partner+User+Management+and+Exceptional+Access