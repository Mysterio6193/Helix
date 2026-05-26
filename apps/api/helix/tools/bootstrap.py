"""Register all built-in tool adapters into the registry.

Run as `python -m helix.tools.bootstrap` to populate the registry at startup.
Also invoked from the FastAPI lifespan.
"""
from __future__ import annotations

from helix.core.logging import get_logger
from helix.tools.adapters.analytics_extra import (
    MixpanelApiTool,
    OpenTableApiTool,
    ResyApiTool,
)
from helix.tools.adapters.deploy import GithubRepoTool, VercelDeployTool
from helix.tools.adapters.image import (
    FluxImageTool,
    FluxSchnellTool,
    OpenAIImageTool,
    SDXLImageTool,
)
from helix.tools.adapters.llm import (
    AnthropicChatTool,
    GeminiChatTool,
    OpenAIChatTool,
    OpenRouterChatTool,
)
from helix.tools.adapters.marketing import (
    GoogleBusinessApiTool,
    HubSpotApiTool,
    MailchimpApiTool,
    SendGridApiTool,
)
from helix.tools.adapters.messaging import (
    DiscordApiTool,
    InstagramApiTool,
    MetaPagesApiTool,
    SlackApiTool,
    TelegramApiTool,
    WhatsAppApiTool,
)
from helix.tools.adapters.new_integrations import (
    AhrefsApiTool,
    AmplitudeApiTool,
    AwsApiTool,
    BigCommerceApiTool,
    FramerApiTool,
    GoogleAdsApiTool,
    GoogleCalendarApiTool,
    IntercomApiTool,
    JiraApiTool,
    LoomApiTool,
    Microsoft365ApiTool,
    PayPalApiTool,
    QuickBooksApiTool,
    RedditAdsApiTool,
    SalesforceApiTool,
    SegmentApiTool,
    SemrushApiTool,
    SnapchatAdsApiTool,
    SquarespaceApiTool,
    TypeformApiTool,
    WebflowApiTool,
    WixApiTool,
    ZendeskApiTool,
)
from helix.tools.adapters.pos_systems import (
    ChowNowApiTool,
    CloverApiTool,
    LightspeedApiTool,
    OrdermarkApiTool,
    PetpoojaApiTool,
    RevelApiTool,
    SliceApiTool,
)
from helix.tools.adapters.productivity import (
    CanvaConnectTool,
    FigmaApiTool,
    GmailDraftTool,
    NotionApiTool,
    WebSearchTool,
)
from helix.tools.adapters.productivity_extra import (
    AirtableApiTool,
    AsanaApiTool,
    CalendlyApiTool,
    LinearApiTool,
)
from helix.tools.adapters.restaurant import (
    DoorDashApiTool,
    SquareApiTool,
    ToastApiTool,
    UberEatsApiTool,
    YelpApiTool,
)
from helix.tools.adapters.saas import (
    Ga4ApiTool,
    KlaviyoApiTool,
    LinkedInApiTool,
    MetaAdsApiTool,
    ShopifyApiTool,
    StripeApiTool,
    TwilioSmsTool,
    WooCommerceApiTool,
    YouTubeApiTool,
)
from helix.tools.adapters.social import (
    PinterestApiTool,
    PostHogApiTool,
    ThreadsApiTool,
    TikTokApiTool,
    TwitterApiTool,
)
from helix.tools.adapters.zoho import (
    ZohoBooksApiTool,
    ZohoCampaignsApiTool,
    ZohoCrmApiTool,
    ZohoDeskApiTool,
    ZohoInventoryApiTool,
    ZohoProjectsApiTool,
    ZohoSubscriptionsApiTool,
)
from helix.tools.registry import clear_registry, list_tools, register_tool

log = get_logger(__name__)


_BUILTINS = (
    # LLM
    OpenAIChatTool,
    AnthropicChatTool,
    GeminiChatTool,
    OpenRouterChatTool,
    # Image
    OpenAIImageTool,
    FluxImageTool,
    FluxSchnellTool,
    SDXLImageTool,
    # Deploy
    GithubRepoTool,
    VercelDeployTool,
    # Productivity
    CanvaConnectTool,
    FigmaApiTool,
    NotionApiTool,
    GmailDraftTool,
    WebSearchTool,
    # SaaS / E-commerce
    ShopifyApiTool,
    WooCommerceApiTool,
    KlaviyoApiTool,
    MetaAdsApiTool,
    StripeApiTool,
    TwilioSmsTool,
    LinkedInApiTool,
    YouTubeApiTool,
    Ga4ApiTool,
    # Messaging
    SlackApiTool,
    DiscordApiTool,
    WhatsAppApiTool,
    MetaPagesApiTool,
    InstagramApiTool,
    TelegramApiTool,
    # Restaurant / POS
    ToastApiTool,
    SquareApiTool,
    DoorDashApiTool,
    UberEatsApiTool,
    YelpApiTool,
    # Marketing
    MailchimpApiTool,
    HubSpotApiTool,
    SendGridApiTool,
    GoogleBusinessApiTool,
    # Productivity
    AirtableApiTool,
    LinearApiTool,
    AsanaApiTool,
    CalendlyApiTool,
    # Social / Analytics
    TwitterApiTool,
    PostHogApiTool,
    ThreadsApiTool,
    TikTokApiTool,
    PinterestApiTool,
    # More analytics
    MixpanelApiTool,
    ResyApiTool,
    OpenTableApiTool,
    # New CRM & Support
    SalesforceApiTool,
    ZendeskApiTool,
    IntercomApiTool,
    JiraApiTool,
    # New Marketing & Ads
    GoogleAdsApiTool,
    SnapchatAdsApiTool,
    RedditAdsApiTool,
    SemrushApiTool,
    AhrefsApiTool,
    # New E-commerce & Payments
    PayPalApiTool,
    QuickBooksApiTool,
    SquarespaceApiTool,
    WixApiTool,
    BigCommerceApiTool,
    # New Productivity & Design
    Microsoft365ApiTool,
    TypeformApiTool,
    WebflowApiTool,
    FramerApiTool,
    LoomApiTool,
    # New Analytics & Data
    SegmentApiTool,
    AmplitudeApiTool,
    GoogleCalendarApiTool,
    AwsApiTool,
    # POS Systems
    PetpoojaApiTool,
    CloverApiTool,
    LightspeedApiTool,
    RevelApiTool,
    ChowNowApiTool,
    OrdermarkApiTool,
    SliceApiTool,
    # Zoho Suite
    ZohoCrmApiTool,
    ZohoBooksApiTool,
    ZohoCampaignsApiTool,
    ZohoDeskApiTool,
    ZohoInventoryApiTool,
    ZohoSubscriptionsApiTool,
    ZohoProjectsApiTool,
)


def bootstrap_tools(*, reset: bool = False) -> list[str]:
    """Instantiate and register every built-in tool. Returns registered names."""
    if reset:
        clear_registry()
    for cls in _BUILTINS:
        try:
            register_tool(cls())
        except Exception:
            log.exception("tool_register_failed", extra={"tool": cls.__name__})
    names = [t.name for t in list_tools()]
    log.info("tools_bootstrapped", extra={"count": len(names), "names": names})
    return names


if __name__ == "__main__":
    names = bootstrap_tools(reset=True)
    for _n in names:
        pass
