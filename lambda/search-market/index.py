import json
import logging
import os

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

def lambda_handler(event, context):
    """Search for market data and comparable products."""
    try:
        product_type = event.get('product_type', '')
        logger.info(f"Searching market data for: {product_type}")
        
        if 'bond' in product_type.lower():
            market_data = {
                "productType": product_type,
                "marketSummary": "Government bond yields have stabilized in Q4 2025 following the Bank of England's recent policy decisions. Investor appetite for safe-haven assets remains strong amid global economic uncertainty.",
                "yieldTrends": {
                    "current": "4.75%",
                    "3MonthAvg": "4.62%",
                    "6MonthAvg": "4.55%",
                    "1YearAvg": "4.40%",
                    "trend": "Upward - yields have increased 35 basis points over the past year"
                },
                "comparableProducts": [
                    {
                        "name": "UK Government Bond Series X",
                        "yield": "4.50%",
                        "maturity": "7 years",
                        "creditRating": "AA"
                    },
                    {
                        "name": "UK Government Bond Series Z",
                        "yield": "5.00%",
                        "maturity": "15 years",
                        "creditRating": "AA"
                    },
                    {
                        "name": "German Government Bund",
                        "yield": "3.80%",
                        "maturity": "10 years",
                        "creditRating": "AAA"
                    },
                    {
                        "name": "US Treasury Bond",
                        "yield": "4.90%",
                        "maturity": "10 years",
                        "creditRating": "AA+"
                    }
                ],
                "description": "The UK government bond market shows healthy demand with competitive yields relative to European peers. Series Y's 4.75% yield positions it attractively in the 10-year maturity segment, offering a premium over German Bunds while maintaining strong credit quality. Current market conditions favor fixed-income investments as central banks signal a pause in rate adjustments."
            }
        else:
            market_data = {
                "productType": product_type,
                "description": f"Market data for {product_type} is currently unavailable. Please contact your financial advisor.",
                "comparableProducts": []
            }
        
        return {
            'statusCode': 200,
            'body': json.dumps({'marketData': market_data})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
