import asyncio
from helix.tools.bootstrap import bootstrap_tools
from helix.tools.registry import get_tool

async def main():
    # Bootstrap all tools (registers browser_use and stagehand)
    print("Bootstrapping tools registry...")
    bootstrap_tools(reset=True)
    
    # 1. Test BrowserUseTool
    browser_tool = get_tool("browser_use")
    if browser_tool:
        print("\n--- Testing BrowserUseTool ---")
        instruction = "Go to https://news.ycombinator.com and extract the top headline."
        print(f"Instruction: '{instruction}'")
        result = await browser_tool.call(instruction=instruction)
        print(f"Success: {result.ok}")
        if result.ok:
            print(f"Mode: {result.data.get('mode')}")
            print(f"Summary: {result.data.get('summary')}")
            if "steps_executed" in result.data:
                print("Steps taken:")
                for step in result.data["steps_executed"]:
                    print(f"  - {step}")
        else:
            print(f"Error: {result.error}")
    else:
        print("Error: 'browser_use' tool not registered!")

    # 2. Test StagehandTool
    stagehand_tool = get_tool("stagehand")
    if stagehand_tool:
        print("\n--- Testing StagehandTool (Shopify) ---")
        result_shopify = await stagehand_tool.call(
            target_site="shopify",
            action="edit_product",
            payload={"product_id": "prod_coffee_101", "title": "Artisanal Cold Brew Coffee"}
        )
        print(f"Success: {result_shopify.ok}")
        if result_shopify.ok:
            data = result_shopify.data
            print(f"Target: {data.get('target')}, Action: {data.get('action')}")
            print(f"Message: {data.get('result', {}).get('message')}")
            print(f"URL: {data.get('result', {}).get('url')}")
            
        print("\n--- Testing StagehandTool (Meta Ads) ---")
        result_meta = await stagehand_tool.call(
            target_site="meta_ads",
            action="create_campaign",
            payload={"budget": 150}
        )
        print(f"Success: {result_meta.ok}")
        if result_meta.ok:
            data = result_meta.data
            print(f"Target: {data.get('target')}, Action: {data.get('action')}")
            print(f"Message: {data.get('result', {}).get('message')}")
            print(f"Adset ID: {data.get('result', {}).get('adset_id')}")
    else:
        print("Error: 'stagehand' tool not registered!")

if __name__ == "__main__":
    asyncio.run(main())
