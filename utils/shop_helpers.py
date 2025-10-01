import re
from urllib.parse import urlparse
from typing import Dict, Optional


def extract_shop_name_from_url(url: str) -> Optional[str]:
    try:
        parsed_url = urlparse(url)
        
        if 'etsy.com' not in parsed_url.netloc:
            return None
            
        path = parsed_url.path
        
        if parsed_url.query:
            query_params = parsed_url.query.split('&')
            for param in query_params:
                if param.startswith('shop_name='):
                    return param.split('=')[1]
        
        shop_match = re.search(r'/shop/([^/]+)', path)
        if shop_match:
            return shop_match.group(1)
            
        return None
        
    except Exception as e:
        print(f"❌ Ошибка при извлечении названия магазина из URL {url}: {e}")
        return None


def extract_shop_names_from_results(results: Dict) -> Dict[str, str]:
    listing_to_shop = {}
    
    try:
        if 'shops' in results:
            for shop_name, products in results['shops'].items():
                for listing_id, url in products.items():
                    listing_to_shop[listing_id] = shop_name
        
        if 'new_products' in results:
            for listing_id, url in results['new_products'].items():
                if listing_id not in listing_to_shop:
                    found_shop = None
                    if 'shops' in results:
                        for shop_name, products in results['shops'].items():
                            for existing_listing_id, existing_url in products.items():
                                if _urls_from_same_shop(url, existing_url):
                                    found_shop = shop_name
                                    break
                            if found_shop:
                                break
                    
                    if found_shop:
                        listing_to_shop[listing_id] = found_shop
                    else:
                        shop_name = extract_shop_name_from_url(url)
                        if shop_name:
                            listing_to_shop[listing_id] = shop_name
                        else:
                            listing_to_shop[listing_id] = "Unknown"
        
        return listing_to_shop
        
    except Exception as e:
        print(f"❌ Ошибка при извлечении названий магазинов: {e}")
        return {}


def _urls_from_same_shop(url1: str, url2: str) -> bool:
    try:
        from urllib.parse import urlparse, parse_qs
        
        parsed1 = urlparse(url1)
        parsed2 = urlparse(url2)
        
        query1 = parse_qs(parsed1.query)
        query2 = parse_qs(parsed2.query)
        
        ref1 = query1.get('ref', [''])[0]
        ref2 = query2.get('ref', [''])[0]
        
        if ref1 and ref2 and 'shop_home_active' in ref1 and 'shop_home_active' in ref2:
            return True
            
        return False
        
    except Exception:
        return False


def get_shop_name_for_product(listing_id: str, url: str, results: Dict = None) -> str:
    if results:
        listing_to_shop = extract_shop_names_from_results(results)
        if listing_id in listing_to_shop:
            return listing_to_shop[listing_id]
    
    shop_name = extract_shop_name_from_url(url)
    return shop_name if shop_name else "Unknown"