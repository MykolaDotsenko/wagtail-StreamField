# Official Reference Library

Use primary/official documentation before blogs, snippets or copied examples.

The repository currently targets Django 5.2 and Wagtail 7.x. Prefer version-matched docs for framework behavior.

## Django 5.2

Main documentation:
- https://docs.djangoproject.com/en/5.2/

Models:
- https://docs.djangoproject.com/en/5.2/topics/db/models/
- https://docs.djangoproject.com/en/5.2/ref/models/constraints/
- https://docs.djangoproject.com/en/5.2/topics/db/transactions/
- https://docs.djangoproject.com/en/5.2/topics/db/optimization/

Forms and validation:
- https://docs.djangoproject.com/en/5.2/topics/forms/
- https://docs.djangoproject.com/en/5.2/ref/forms/validation/

Authentication / authorization:
- https://docs.djangoproject.com/en/5.2/topics/auth/
- https://docs.djangoproject.com/en/5.2/topics/auth/default/

Security:
- https://docs.djangoproject.com/en/5.2/topics/security/
- https://docs.djangoproject.com/en/5.2/ref/csrf/
- https://docs.djangoproject.com/en/5.2/ref/middleware/#module-django.middleware.security

Testing:
- https://docs.djangoproject.com/en/5.2/topics/testing/
- https://docs.djangoproject.com/en/5.2/topics/testing/tools/

Deployment:
- https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/
- https://docs.djangoproject.com/en/5.2/howto/static-files/deployment/

## Wagtail 7.0

Usage guide:
- https://docs.wagtail.org/en/7.0/topics/

Page models:
- https://docs.wagtail.org/en/7.0/topics/pages.html

StreamField:
- https://docs.wagtail.org/en/7.0/topics/streamfield.html

Snippets:
- https://docs.wagtail.org/en/7.0/topics/snippets/

Search:
- https://docs.wagtail.org/en/7.0/topics/search/

Images:
- https://docs.wagtail.org/en/7.0/topics/images.html

Customizing Wagtail:
- https://docs.wagtail.org/en/7.0/advanced_topics/customization/

Hooks:
- https://docs.wagtail.org/en/7.0/reference/hooks.html

Accessibility considerations:
- https://docs.wagtail.org/en/7.0/advanced_topics/accessibility_considerations.html

Testing:
- https://docs.wagtail.org/en/7.0/advanced_topics/testing.html

## Accessibility

WCAG 2.2:
- https://www.w3.org/TR/WCAG22/

Understanding WCAG 2.2:
- https://www.w3.org/WAI/WCAG22/Understanding/

Relevant criteria:
- 1.4.3 Contrast (Minimum)
- 1.4.11 Non-text Contrast
- 1.4.12 Text Spacing
- 1.4.13 Content on Hover or Focus
- 2.1.1 Keyboard
- 2.4.3 Focus Order
- 2.4.7 Focus Visible
- 2.4.11 Focus Not Obscured (Minimum)
- 2.5.7 Dragging Movements
- 2.5.8 Target Size (Minimum)
- 3.3.1 Error Identification
- 3.3.2 Labels or Instructions
- 4.1.2 Name, Role, Value
- 4.1.3 Status Messages

WAI form tutorials:
- https://www.w3.org/WAI/tutorials/forms/

ARIA Authoring Practices:
- https://www.w3.org/WAI/ARIA/apg/

Important rule:
Use native HTML first. ARIA supplements semantics; it does not replace correct native elements.

## Web platform references

MDN:
- https://developer.mozilla.org/

Reduced motion:
- https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-reduced-motion

Responsive images:
- https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Performance/Multimedia

## Security

OWASP Cheat Sheet Series:
- https://cheatsheetseries.owasp.org/

OWASP ASVS:
- https://owasp.org/www-project-application-security-verification-standard/

Use OWASP as supplemental security guidance; Django's versioned security documentation remains authoritative for framework-specific behavior.

## Python

Python documentation:
- https://docs.python.org/3/

Packaging:
- https://packaging.python.org/

## GitHub Actions

Official documentation:
- https://docs.github.com/en/actions

Security hardening:
- https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions

## Reference policy

Before introducing a framework feature:
1. Open the version-matched official page.
2. Confirm API/behavior against the installed version.
3. Prefer documented extension points.
4. Add a link here if the source becomes recurrently relevant.
5. If a choice is materially architectural, record it in `09_ADR_LOG.md`.

Do not cargo-cult code from tutorials when official APIs solve the problem directly.
