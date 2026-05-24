"""Integration provider catalog.

Supports two auth kinds:
- `oauth2`: standard authorization-code flow with the existing oauth_flow helpers.
- `token`:  user-pasted secret (e.g. Telegram bot token, restaurant POS API key).

Providers carry a `category` so the integrations UI can group them.
Providers without env-side client credentials still appear in the catalog
(so users can see what's available) but `configured=False` blocks Connect.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class OAuthProvider:
    key: str
    display_name: str
    authorize_url: str = ""
    token_url: str = ""
    scopes: list[str] = field(default_factory=list)
    scope_separator: str = " "
    auth_kind: str = "oauth2"  # oauth2 | token
    extra_authorize_params: dict[str, str] = field(default_factory=dict)
    extra_token_params: dict[str, str] = field(default_factory=dict)
    uses_basic_auth_for_token: bool = False
    token_body_format: str = "form"  # form | json
    revoke_url: str | None = None
    # New fields
    category: str = "productivity"
    icon: str = ""  # emoji or short tag (frontend uses fallback when empty)
    description: str = ""
    token_label: str = "API Token"  # for auth_kind=token UI
    token_help_url: str = ""
    coming_soon: bool = False  # show in catalog, disable connect


# ──────────────────────────────────────────────────────────────────────────
# OAuth2 providers — fully wired through helix.integrations.oauth_flow
# ──────────────────────────────────────────────────────────────────────────

_OAUTH: dict[str, OAuthProvider] = {
    "canva": OAuthProvider(
        key="canva",
        display_name="Canva",
        category="design",
        icon="🎨",
        description="Design boards, brand kits, and asset library.",
        authorize_url="https://www.canva.com/api/oauth/authorize",
        token_url="https://api.canva.com/rest/v1/oauth/token",
        scopes=["design:content:read", "design:content:write", "asset:read", "asset:write"],
        uses_basic_auth_for_token=True,
        extra_authorize_params={"response_type": "code"},
    ),
    "figma": OAuthProvider(
        key="figma",
        display_name="Figma",
        category="design",
        icon="✏️",
        description="Read frames and component libraries for design hand-off.",
        authorize_url="https://www.figma.com/oauth",
        token_url="https://www.figma.com/api/oauth/token",
        scopes=["file_read"],
        scope_separator=",",
        extra_authorize_params={"response_type": "code"},
    ),
    "notion": OAuthProvider(
        key="notion",
        display_name="Notion",
        category="productivity",
        icon="📓",
        description="Publish briefs and creative wikis to Notion.",
        authorize_url="https://api.notion.com/v1/oauth/authorize",
        token_url="https://api.notion.com/v1/oauth/token",
        scopes=[],
        uses_basic_auth_for_token=True,
        token_body_format="json",
        extra_authorize_params={"response_type": "code", "owner": "user"},
    ),
    "google": OAuthProvider(
        key="google",
        display_name="Gmail (Google)",
        category="productivity",
        icon="✉️",
        description="Draft campaign emails directly in Gmail.",
        authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
        token_url="https://oauth2.googleapis.com/token",
        scopes=[
            "https://www.googleapis.com/auth/gmail.compose",
            "https://www.googleapis.com/auth/userinfo.email",
            "openid",
        ],
        extra_authorize_params={
            "response_type": "code",
            "access_type": "offline",
            "prompt": "consent",
        },
        revoke_url="https://oauth2.googleapis.com/revoke",
    ),
}


# ──────────────────────────────────────────────────────────────────────────
# Token providers — user pastes an API key/secret/token
# ──────────────────────────────────────────────────────────────────────────

_TOKEN: dict[str, OAuthProvider] = {
    # Messaging
    "telegram": OAuthProvider(
        key="telegram",
        display_name="Telegram",
        category="messaging",
        icon="✈️",
        description="Chat with Helix from any Telegram client via your own bot.",
        auth_kind="token",
        token_label="Bot Token",
        token_help_url="https://core.telegram.org/bots#how-do-i-create-a-bot",
    ),
    "slack": OAuthProvider(
        key="slack",
        display_name="Slack",
        category="messaging",
        icon="💬",
        description="Post run updates and pull conversations from Slack.",
        auth_kind="token",
        token_label="Bot User OAuth Token (xoxb-…)",
        token_help_url="https://api.slack.com/apps",
    ),
    "discord": OAuthProvider(
        key="discord",
        display_name="Discord",
        category="messaging",
        icon="🎮",
        description="Bot integration for community channels.",
        auth_kind="token",
        token_label="Bot Token",
        token_help_url="https://discord.com/developers/applications",
    ),
    "whatsapp_business": OAuthProvider(
        key="whatsapp_business",
        display_name="WhatsApp Business",
        category="messaging",
        icon="📱",
        description="Send marketing + customer messages via Meta Cloud API.",
        auth_kind="token",
        token_label="Permanent Access Token",
        token_help_url="https://developers.facebook.com/docs/whatsapp/cloud-api/get-started",
    ),
    # Meta family
    "meta_pages": OAuthProvider(
        key="meta_pages",
        display_name="Facebook Pages",
        category="meta",
        icon="📘",
        description="Schedule posts, read insights, run page replies.",
        auth_kind="token",
        token_label="Page Access Token",
        token_help_url="https://developers.facebook.com/tools/explorer/",
    ),
    "instagram_business": OAuthProvider(
        key="instagram_business",
        display_name="Instagram Business",
        category="meta",
        icon="📷",
        description="Publish to feed/Reels, read DM + insights via Graph API.",
        auth_kind="token",
        token_label="IG User Access Token",
        token_help_url="https://developers.facebook.com/docs/instagram-api",
    ),
    "meta_ads": OAuthProvider(
        key="meta_ads",
        display_name="Meta Ads",
        category="meta",
        icon="📊",
        description="Create + report Facebook/Instagram ad campaigns.",
        auth_kind="token",
        token_label="Marketing API Token",
        token_help_url="https://developers.facebook.com/docs/marketing-apis",
    ),
    "threads": OAuthProvider(
        key="threads",
        display_name="Threads",
        category="meta",
        icon="🧵",
        description="Cross-post to Threads via Meta API.",
        auth_kind="token",
        token_label="Threads Access Token",
        token_help_url="https://developers.facebook.com/docs/threads",
        coming_soon=True,
    ),
    # Restaurant / POS
    "toast": OAuthProvider(
        key="toast",
        display_name="Toast POS",
        category="restaurant",
        icon="🍞",
        description="Menu sync, order history, loyalty data.",
        auth_kind="token",
        token_label="API Client Secret",
        token_help_url="https://doc.toasttab.com/openapi/",
    ),
    "square": OAuthProvider(
        key="square",
        display_name="Square",
        category="restaurant",
        icon="◼️",
        description="Items, payments, inventory, loyalty.",
        auth_kind="token",
        token_label="Access Token",
        token_help_url="https://developer.squareup.com/apps",
    ),
    "resy": OAuthProvider(
        key="resy",
        display_name="Resy",
        category="restaurant",
        icon="🍽️",
        description="Reservations, covers, guest history.",
        auth_kind="token",
        token_label="API Key",
        coming_soon=True,
    ),
    "opentable": OAuthProvider(
        key="opentable",
        display_name="OpenTable",
        category="restaurant",
        icon="📖",
        description="Reservations + diner profiles.",
        auth_kind="token",
        token_label="Partner Token",
        coming_soon=True,
    ),
    "doordash": OAuthProvider(
        key="doordash",
        display_name="DoorDash Drive",
        category="restaurant",
        icon="🛵",
        description="Delivery orchestration + menu sync.",
        auth_kind="token",
        token_label="JWT Signing Secret",
        token_help_url="https://developer.doordash.com/",
    ),
    "ubereats": OAuthProvider(
        key="ubereats",
        display_name="Uber Eats",
        category="restaurant",
        icon="🥡",
        description="Store, menu, and order webhooks.",
        auth_kind="token",
        token_label="OAuth Access Token",
        token_help_url="https://developer.uber.com/docs/eats",
    ),
    "yelp": OAuthProvider(
        key="yelp",
        display_name="Yelp Fusion",
        category="restaurant",
        icon="⭐",
        description="Reviews + business profile management.",
        auth_kind="token",
        token_label="Fusion API Key",
        token_help_url="https://www.yelp.com/developers",
    ),
    "google_business": OAuthProvider(
        key="google_business",
        display_name="Google Business Profile",
        category="restaurant",
        icon="📍",
        description="Posts, reviews, photos for Google Maps presence.",
        auth_kind="token",
        token_label="OAuth Access Token",
        token_help_url="https://developers.google.com/my-business",
    ),
    # E-commerce
    "shopify": OAuthProvider(
        key="shopify",
        display_name="Shopify",
        category="ecommerce",
        icon="🛍️",
        description="Storefront, products, orders, abandoned-cart.",
        auth_kind="token",
        token_label="Admin API Access Token",
        token_help_url="https://shopify.dev/docs/api/admin",
    ),
    "stripe": OAuthProvider(
        key="stripe",
        display_name="Stripe",
        category="ecommerce",
        icon="💳",
        description="Payments, invoices, billing automation.",
        auth_kind="token",
        token_label="Secret API Key (sk_…)",
        token_help_url="https://dashboard.stripe.com/apikeys",
    ),
    "woocommerce": OAuthProvider(
        key="woocommerce",
        display_name="WooCommerce",
        category="ecommerce",
        icon="🛒",
        description="WordPress-based store + REST API.",
        auth_kind="token",
        token_label="Consumer Key:Secret",
        token_help_url="https://woocommerce.com/document/rest-api/",
    ),
    # Marketing
    "mailchimp": OAuthProvider(
        key="mailchimp",
        display_name="Mailchimp",
        category="marketing",
        icon="📬",
        description="Email lists, automations, journeys.",
        auth_kind="token",
        token_label="API Key",
        token_help_url="https://us1.admin.mailchimp.com/account/api/",
    ),
    "klaviyo": OAuthProvider(
        key="klaviyo",
        display_name="Klaviyo",
        category="marketing",
        icon="📈",
        description="E-commerce CRM, segmentation, flows.",
        auth_kind="token",
        token_label="Private API Key",
        token_help_url="https://www.klaviyo.com/account#api-keys-tab",
    ),
    "hubspot": OAuthProvider(
        key="hubspot",
        display_name="HubSpot",
        category="marketing",
        icon="🧲",
        description="CRM contacts, deals, marketing.",
        auth_kind="token",
        token_label="Private App Token",
        token_help_url="https://developers.hubspot.com/docs/api/private-apps",
    ),
    "sendgrid": OAuthProvider(
        key="sendgrid",
        display_name="SendGrid",
        category="marketing",
        icon="🛫",
        description="Transactional + bulk email API.",
        auth_kind="token",
        token_label="API Key (SG.…)",
        token_help_url="https://app.sendgrid.com/settings/api_keys",
    ),
    # Social
    "linkedin": OAuthProvider(
        key="linkedin",
        display_name="LinkedIn",
        category="social",
        icon="💼",
        description="Company page posts + ad campaigns.",
        auth_kind="token",
        token_label="Access Token",
        token_help_url="https://developer.linkedin.com/",
    ),
    "twitter": OAuthProvider(
        key="twitter",
        display_name="X / Twitter",
        category="social",
        icon="✖️",
        description="Tweet drafts, threads, listening.",
        auth_kind="token",
        token_label="Bearer Token",
        token_help_url="https://developer.twitter.com/",
    ),
    "tiktok_business": OAuthProvider(
        key="tiktok_business",
        display_name="TikTok Business",
        category="social",
        icon="🎵",
        description="Creator content + Spark Ads campaigns.",
        auth_kind="token",
        token_label="Access Token",
        coming_soon=True,
    ),
    "youtube": OAuthProvider(
        key="youtube",
        display_name="YouTube",
        category="social",
        icon="▶️",
        description="Upload videos, manage channel, comments.",
        auth_kind="token",
        token_label="OAuth Access Token",
        token_help_url="https://developers.google.com/youtube/registering_an_application",
    ),
    "pinterest": OAuthProvider(
        key="pinterest",
        display_name="Pinterest",
        category="social",
        icon="📌",
        description="Pin scheduling and analytics.",
        auth_kind="token",
        token_label="Access Token",
        coming_soon=True,
    ),
    # Productivity / project
    "airtable": OAuthProvider(
        key="airtable",
        display_name="Airtable",
        category="productivity",
        icon="🗂️",
        description="Operational bases for content + campaigns.",
        auth_kind="token",
        token_label="Personal Access Token",
        token_help_url="https://airtable.com/create/tokens",
    ),
    "linear": OAuthProvider(
        key="linear",
        display_name="Linear",
        category="productivity",
        icon="📐",
        description="Issues + cycles for product/eng tasks.",
        auth_kind="token",
        token_label="Personal API Key",
        token_help_url="https://linear.app/settings/api",
    ),
    "asana": OAuthProvider(
        key="asana",
        display_name="Asana",
        category="productivity",
        icon="🧷",
        description="Tasks + projects + timelines.",
        auth_kind="token",
        token_label="Personal Access Token",
        token_help_url="https://app.asana.com/0/my-apps",
    ),
    "calendly": OAuthProvider(
        key="calendly",
        display_name="Calendly",
        category="productivity",
        icon="🗓️",
        description="Booking links + event types.",
        auth_kind="token",
        token_label="Personal Access Token",
        token_help_url="https://calendly.com/integrations/api_webhooks",
    ),
    # Analytics
    "posthog": OAuthProvider(
        key="posthog",
        display_name="PostHog",
        category="analytics",
        icon="📊",
        description="Product analytics + experiments.",
        auth_kind="token",
        token_label="Personal API Key",
        token_help_url="https://app.posthog.com/settings/user-api-keys",
    ),
    "mixpanel": OAuthProvider(
        key="mixpanel",
        display_name="Mixpanel",
        category="analytics",
        icon="📉",
        description="Funnels, retention, cohorts.",
        auth_kind="token",
        token_label="Service Account Secret",
        coming_soon=True,
    ),
    "ga4": OAuthProvider(
        key="ga4",
        display_name="Google Analytics 4",
        category="analytics",
        icon="📈",
        description="Web + app traffic insights.",
        auth_kind="token",
        token_label="OAuth Access Token",
        token_help_url="https://developers.google.com/analytics/devguides/reporting/data/v1",
    ),
}


PROVIDERS: dict[str, OAuthProvider] = {**_OAUTH, **_TOKEN}


def get_provider(key: str) -> OAuthProvider | None:
    return PROVIDERS.get(key)


def list_providers() -> list[OAuthProvider]:
    return list(PROVIDERS.values())


def provider_to_public(p: OAuthProvider) -> dict[str, Any]:
    return {
        "key": p.key,
        "display_name": p.display_name,
        "scopes": list(p.scopes),
        "auth_kind": p.auth_kind,
        "category": p.category,
        "icon": p.icon,
        "description": p.description,
        "token_label": p.token_label if p.auth_kind == "token" else None,
        "token_help_url": p.token_help_url if p.auth_kind == "token" else None,
        "coming_soon": p.coming_soon,
    }
