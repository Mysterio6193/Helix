from pathlib import Path

EXTENDED_SKILLS = [
    # Social / Ads
    {
        "name": "pinterest_ads",
        "description": "Design Promoted Pins and write conversion-optimized copy. Trigger phrases: 'pinterest ads', 'promoted pin'.",
        "required_tools": ["openai_chat", "flux_schnell"],
        "tags": ["social", "ads"],
        "trigger_phrases": ["pinterest ads", "promoted pin"]
    },
    {
        "name": "tiktok_spark_ads",
        "description": "Generate hook script and target profile for Spark Ads. Trigger phrases: 'spark ads', 'tiktok hook'.",
        "required_tools": ["openai_chat"],
        "tags": ["social", "ads"],
        "trigger_phrases": ["spark ads", "tiktok hook"]
    },
    {
        "name": "linkedin_sponsored_content",
        "description": "Draft professional lead-gen posts for sponsored B2B campaigns. Trigger phrases: 'linkedin sponsor', 'sponsored content'.",
        "required_tools": ["openai_chat"],
        "tags": ["social", "ads"],
        "trigger_phrases": ["linkedin sponsor", "sponsored content"]
    },
    {
        "name": "reddit_sponsored_posts",
        "description": "Draft conversational text and headlines for Reddit campaigns. Trigger phrases: 'reddit ads', 'reddit sponsored'.",
        "required_tools": ["openai_chat"],
        "tags": ["social", "ads"],
        "trigger_phrases": ["reddit ads", "reddit sponsored"]
    },
    {
        "name": "meta_lead_ads",
        "description": "Build high-converting forms and headlines for Facebook Lead Ads. Trigger phrases: 'facebook lead ads', 'meta lead gen'.",
        "required_tools": ["openai_chat"],
        "tags": ["social", "ads"],
        "trigger_phrases": ["facebook lead ads", "meta lead gen"]
    },
    # Email / SMS
    {
        "name": "newsletter_weekly",
        "description": "Compose engaging weekly newsletters with custom product highlights. Trigger phrases: 'weekly newsletter', 'email newsletter'.",
        "required_tools": ["openai_chat"],
        "tags": ["email", "marketing"],
        "trigger_phrases": ["weekly newsletter", "email newsletter"]
    },
    {
        "name": "product_launch_email",
        "description": "Write persuasive product launch sequences to generate early sales. Trigger phrases: 'launch email', 'new product email'.",
        "required_tools": ["openai_chat"],
        "tags": ["email", "marketing"],
        "trigger_phrases": ["launch email", "new product email"]
    },
    {
        "name": "customer_survey_email",
        "description": "Craft email asking for reviews or customer feedback with incentive offers. Trigger phrases: 'feedback survey', 'review request email'.",
        "required_tools": ["openai_chat"],
        "tags": ["email", "marketing"],
        "trigger_phrases": ["feedback survey", "review request email"]
    },
    {
        "name": "vip_rewards_email",
        "description": "Draft customized reward emails for high-tier loyal customers. Trigger phrases: 'vip email', 'loyalty reward email'.",
        "required_tools": ["openai_chat"],
        "tags": ["email", "marketing"],
        "trigger_phrases": ["vip email", "loyalty reward email"]
    },
    {
        "name": "cross_sell_sms",
        "description": "Draft short, impactful cross-sell SMS messages based on purchase history. Trigger phrases: 'cross sell sms', 'text promo'.",
        "required_tools": ["openai_chat"],
        "tags": ["sms", "marketing"],
        "trigger_phrases": ["cross sell sms", "text promo"]
    },
    # SEO / Content
    {
        "name": "local_seo_schema",
        "description": "Generate LocalBusiness schema markup for restaurant/retail sites. Trigger phrases: 'local schema', 'business schema'.",
        "required_tools": ["openai_chat"],
        "tags": ["seo", "schema"],
        "trigger_phrases": ["local schema", "business schema"]
    },
    {
        "name": "google_maps_optimization",
        "description": "Draft listing descriptions and update maps details for SEO visibility. Trigger phrases: 'google maps optimization', 'maps ranking'.",
        "required_tools": ["openai_chat"],
        "tags": ["seo", "marketing"],
        "trigger_phrases": ["google maps optimization", "maps ranking"]
    },
    {
        "name": "alt_text_generator",
        "description": "Auto-generate descriptive alt text for product images to improve search SEO. Trigger phrases: 'image alt text', 'alt description'.",
        "required_tools": ["openai_chat"],
        "tags": ["seo", "image"],
        "trigger_phrases": ["image alt text", "alt description"]
    },
    {
        "name": "voice_search_optimization",
        "description": "Optimize copywriting for conversational voice assistant searches (Siri, Alexa). Trigger phrases: 'voice search seo', 'voice optimization'.",
        "required_tools": ["openai_chat"],
        "tags": ["seo", "copy"],
        "trigger_phrases": ["voice search seo", "voice optimization"]
    },
    {
        "name": "press_release_pitch",
        "description": "Write a compelling press release highlighting a major brand milestone. Trigger phrases: 'press release', 'pr pitch'.",
        "required_tools": ["openai_chat"],
        "tags": ["pr", "copy"],
        "trigger_phrases": ["press release", "pr pitch"]
    },
    # Analytics / Operations
    {
        "name": "cohort_retention_report",
        "description": "Analyze and build structured reports on customer retention cohorts. Trigger phrases: 'cohort analysis', 'retention report'.",
        "required_tools": ["openai_chat"],
        "tags": ["analytics", "operations"],
        "trigger_phrases": ["cohort analysis", "retention report"]
    },
    {
        "name": "roas_tracker_dashboard",
        "description": "Extract campaign performance and summarize Return on Ad Spend. Trigger phrases: 'roas tracking', 'roas dashboard'.",
        "required_tools": ["openai_chat"],
        "tags": ["analytics", "ads"],
        "trigger_phrases": ["roas tracking", "roas dashboard"]
    },
    {
        "name": "conversion_funnel_audit",
        "description": "Audit shopping cart checkout funnels for user experience drop-offs. Trigger phrases: 'funnel audit', 'conversion audit'.",
        "required_tools": ["openai_chat"],
        "tags": ["analytics", "cro"],
        "trigger_phrases": ["funnel audit", "conversion audit"]
    },
    {
        "name": "competitor_pricing_scraping",
        "description": "Conduct scraping operations on competitive sites for price matching indexes. Trigger phrases: 'price matching', 'scrape prices'.",
        "required_tools": ["openai_chat"],
        "tags": ["analytics", "pricing"],
        "trigger_phrases": ["price matching", "scrape prices"]
    },
    # Creative / Design
    {
        "name": "infographic_layout",
        "description": "Design layouts for structural data visualization infographics. Trigger phrases: 'infographic', 'data visualization'.",
        "required_tools": ["openai_chat", "flux_schnell"],
        "tags": ["design", "image"],
        "trigger_phrases": ["infographic", "data visualization"]
    },
    {
        "name": "instagram_story_board",
        "description": "Draw story board frames for daily brand Instagram highlights. Trigger phrases: 'story board', 'instagram story'.",
        "required_tools": ["openai_chat", "flux_schnell"],
        "tags": ["design", "image"],
        "trigger_phrases": ["story board", "instagram story"]
    },
    {
        "name": "brand_color_palette",
        "description": "Determine optimized brand palette values matching emotional target school. Trigger phrases: 'brand colors', 'palette creation'.",
        "required_tools": ["openai_chat"],
        "tags": ["design", "brand"],
        "trigger_phrases": ["brand colors", "palette creation"]
    },
    {
        "name": "packaging_die_line",
        "description": "Determine standard box dimensions and print lines for brand boxes. Trigger phrases: 'die line', 'packaging box'.",
        "required_tools": ["openai_chat"],
        "tags": ["design", "packaging"],
        "trigger_phrases": ["die line", "packaging box"]
    },
    {
        "name": "sticker_pack_art",
        "description": "Generate illustration assets for customer loyalty sticker packages. Trigger phrases: 'sticker art', 'sticker illustration'.",
        "required_tools": ["openai_chat", "flux_schnell"],
        "tags": ["design", "image"],
        "trigger_phrases": ["sticker art", "sticker illustration"]
    },
    # Additional E-commerce extended skills
    {
        "name": "shopify_seo_meta",
        "description": "Generate optimized SEO title tags and meta descriptions for Shopify products. Trigger phrases: 'shopify seo', 'shopify meta'.",
        "required_tools": ["openai_chat"],
        "tags": ["seo", "ecommerce"],
        "trigger_phrases": ["shopify seo", "shopify meta"]
    },
    {
        "name": "klaviyo_flow_segment",
        "description": "Construct segment rules for post-purchase winback flows in Klaviyo. Trigger phrases: 'klaviyo flow', 'klaviyo segment'.",
        "required_tools": ["openai_chat"],
        "tags": ["marketing", "ecommerce"],
        "trigger_phrases": ["klaviyo flow", "klaviyo segment"]
    },
    {
        "name": "meta_ads_lookalike",
        "description": "Formulate custom and lookalike audience setups for Meta campaigns. Trigger phrases: 'lookalike audience', 'meta audience'.",
        "required_tools": ["openai_chat"],
        "tags": ["social", "ads"],
        "trigger_phrases": ["lookalike audience", "meta audience"]
    },
    {
        "name": "stripe_invoice_promo",
        "description": "Inject promotional codes and coupons into customer invoice templates. Trigger phrases: 'invoice promo', 'stripe coupons'.",
        "required_tools": ["openai_chat"],
        "tags": ["billing", "ecommerce"],
        "trigger_phrases": ["invoice promo", "stripe coupons"]
    },
    {
        "name": "twilio_cart_recovery",
        "description": "Compose urgent and friendly SMS reminders for abandoned shopping carts. Trigger phrases: 'cart sms recovery', 'abandoned sms'.",
        "required_tools": ["openai_chat"],
        "tags": ["sms", "ecommerce"],
        "trigger_phrases": ["cart sms recovery", "abandoned sms"]
    },
    # Additional operational and growth skills
    {
        "name": "brand_voice_benchmark",
        "description": "Score brand copy variations against established tone of voice guides. Trigger phrases: 'voice score', 'tone benchmark'.",
        "required_tools": ["openai_chat"],
        "tags": ["brand", "copy"],
        "trigger_phrases": ["voice score", "tone benchmark"]
    },
    {
        "name": "influencer_outreach_pitch",
        "description": "Compose personalized collab offers for target nano-influencers. Trigger phrases: 'influencer outreach', 'collab pitch'.",
        "required_tools": ["openai_chat"],
        "tags": ["social", "copy"],
        "trigger_phrases": ["influencer outreach", "collab pitch"]
    },
    {
        "name": "seo_cluster_planning",
        "description": "Organize blog posts into structured parent-child topical authority clusters. Trigger phrases: 'seo clusters', 'topical clusters'.",
        "required_tools": ["openai_chat"],
        "tags": ["seo", "copy"],
        "trigger_phrases": ["seo clusters", "topical clusters"]
    },
    {
        "name": "checkout_ux_checklist",
        "description": "Review storefront checkouts against visual hierarchy heuristics. Trigger phrases: 'checkout ux', 'checkout checklist'.",
        "required_tools": ["openai_chat"],
        "tags": ["cro", "design"],
        "trigger_phrases": ["checkout ux", "checkout checklist"]
    },
    {
        "name": "backlink_prospecting_list",
        "description": "Identify domain prospects and pitch angles for authority backlink building. Trigger phrases: 'backlink building', 'domain prospecting'.",
        "required_tools": ["openai_chat"],
        "tags": ["seo", "marketing"],
        "trigger_phrases": ["backlink building", "domain prospecting"]
    },
    {
        "name": "brand_positioning_matrix",
        "description": "Determine unique selling coordinates relative to four key competitors. Trigger phrases: 'positioning matrix', 'brand coordinates'.",
        "required_tools": ["openai_chat"],
        "tags": ["brand", "operations"],
        "trigger_phrases": ["positioning matrix", "brand coordinates"]
    },
    {
        "name": "user_onboarding_survey",
        "description": "Draft interactive post-sign-up customer segmentation surveys. Trigger phrases: 'onboarding survey', 'user segmentation survey'.",
        "required_tools": ["openai_chat"],
        "tags": ["onboarding", "copy"],
        "trigger_phrases": ["onboarding survey", "user segmentation survey"]
    },
    {
        "name": "sms_flash_sale",
        "description": "Craft copy and schedule parameters for high-urgency flash sale texts. Trigger phrases: 'flash sale sms', 'sms promo'.",
        "required_tools": ["openai_chat"],
        "tags": ["sms", "marketing"],
        "trigger_phrases": ["flash sale sms", "sms promo"]
    },
    {
        "name": "facebook_group_welcome",
        "description": "Draft warm welcoming templates for new brand community joins. Trigger phrases: 'facebook welcome', 'community welcome'.",
        "required_tools": ["openai_chat"],
        "tags": ["social", "copy"],
        "trigger_phrases": ["facebook welcome", "community welcome"]
    },
    {
        "name": "press_kit_curation",
        "description": "Assemble media assets, high-res logo links, and brand brief copy for PR kits. Trigger phrases: 'press kit', 'media kit'.",
        "required_tools": ["openai_chat"],
        "tags": ["brand", "pr"],
        "trigger_phrases": ["press kit", "media kit"]
    },
    {
        "name": "referral_program_rules",
        "description": "Formulate optimized gamified parameters for brand loyalty share loops. Trigger phrases: 'referral program', 'referral rules'.",
        "required_tools": ["openai_chat"],
        "tags": ["marketing", "referrals"],
        "trigger_phrases": ["referral program", "referral rules"]
    },
    {
        "name": "holiday_campaign_calendar",
        "description": "Plan key ad set, email copy, and discount dates across major holidays. Trigger phrases: 'campaign calendar', 'holiday planning'.",
        "required_tools": ["openai_chat"],
        "tags": ["marketing", "operations"],
        "trigger_phrases": ["campaign calendar", "holiday planning"]
    },
    {
        "name": "faq_accordion_copy",
        "description": "Write pre-emptive Q&As based on typical customer support checkout queries. Trigger phrases: 'faq copy', 'checkout faq'.",
        "required_tools": ["openai_chat"],
        "tags": ["web", "copy"],
        "trigger_phrases": ["faq copy", "checkout faq"]
    },
    {
        "name": "value_proposition_slogan",
        "description": "Synthesize a core five-word value statement for storefront headers. Trigger phrases: 'value proposition', 'brand slogan'.",
        "required_tools": ["openai_chat"],
        "tags": ["brand", "copy"],
        "trigger_phrases": ["value proposition", "brand slogan"]
    },
    {
        "name": "packaging_box_insert",
        "description": "Draft thank-you inserts with loyalty coupon codes for delivery boxes. Trigger phrases: 'box insert', 'thank you card'.",
        "required_tools": ["openai_chat"],
        "tags": ["design", "packaging"],
        "trigger_phrases": ["box insert", "thank you card"]
    },
    {
        "name": "product_bundle_builder",
        "description": "Group menu or merchandise inventory items into attractive discounted combos. Trigger phrases: 'product bundle', 'discount combos'.",
        "required_tools": ["openai_chat"],
        "tags": ["pricing", "ecommerce"],
        "trigger_phrases": ["product bundle", "discount combos"]
    }
]

skills_dir = Path("/Users/mihirsachdev/Downloads/MARK FINAL/helix/skills")

for skill in EXTENDED_SKILLS:
    folder = skills_dir / skill["name"]
    folder.mkdir(parents=True, exist_ok=True)
    
    tp_str = "\n".join([f"  - {tp}" for tp in skill["trigger_phrases"]])
    tags_str = "\n".join([f"  - {tg}" for tg in skill["tags"]])
    tools_str = ", ".join(skill["required_tools"])
    
    content = f"""---
name: {skill["name"]}
version: 0.1.0
description: >
  {skill["description"]}
inputs:
  brand_id: {{ type: uuid, required: true }}
  context_override: {{ type: object, required: false }}
outputs:
  result: object
required_tools: [{tools_str}]
dependencies: []
tags:
{tags_str}
trigger_phrases:
{tp_str}
---

# {skill["name"].replace('_', ' ').title()}

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered.
"""
    with open(folder / "SKILL.md", "w") as f:
        f.write(content)

