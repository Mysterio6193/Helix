import asyncio

from helix.tools.bootstrap import bootstrap_tools
from helix.tools.registry import get_tool


async def main():
    # Bootstrap all tools (registers Helix browser operators)
    bootstrap_tools(reset=True)
    
    # 1. Test BrowserUseTool
    browser_tool = get_tool("helix_browser")
    if browser_tool:
        instruction = "Go to https://news.ycombinator.com and extract the top headline."
        result = await browser_tool.call(instruction=instruction)
        if result.ok:
            if "steps_executed" in result.data:
                for _step in result.data["steps_executed"]:
                    pass
        else:
            pass
    else:
        pass

    # 2. Test page operator
    page_operator_tool = get_tool("helix_page_operator")
    if page_operator_tool:
        result_shopify = await page_operator_tool.call(
            target_site="shopify",
            action="edit_product",
            payload={"product_id": "prod_coffee_101", "title": "Artisanal Cold Brew Coffee"}
        )
        if result_shopify.ok:
            pass
            
        result_meta = await page_operator_tool.call(
            target_site="meta_ads",
            action="create_campaign",
            payload={"budget": 150}
        )
        if result_meta.ok:
            pass
    else:
        pass

if __name__ == "__main__":
    asyncio.run(main())
