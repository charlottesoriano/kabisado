"""Clerk webhooks (``POST /webhooks/clerk``), Svix-verified.

``user.created`` / ``user.updated`` upsert the profile; ``user.deleted`` deletes the profile
(cascade) and the user's Storage files. Idempotent by ``svix-id`` via ``app.webhook_events``."""
