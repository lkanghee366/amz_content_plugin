"""paapi_client.py

Amazon Product Advertising API (PA-API) minimal client for SearchItems.
Implements AWS Signature Version 4 signing.

NOTE:
- This is a lightweight implementation (no external deps besides stdlib + requests).
- Handle throttling / transient errors with simple exponential backoff.
- Only the resources we need are requested to keep payload small.
"""
from __future__ import annotations

import datetime
import hashlib
import hmac
import json
import time
from typing import Dict, List, Any, Optional, Tuple

import requests

from config import (
    AMAZON_ACCESS_KEY,
    AMAZON_SECRET_KEY,
    AMAZON_PARTNER_TAG,
    AMAZON_REGION,
)

PAAPI_HOST = "webservices.amazon.com"
PAAPI_ENDPOINT = f"https://{PAAPI_HOST}/paapi5/searchitems"
X_AMZ_TARGET_SEARCH = "com.amazon.paapi5.v1.ProductAdvertisingAPIv1.SearchItems"
X_AMZ_TARGET_GET = "com.amazon.paapi5.v1.ProductAdvertisingAPIv1.GetItems"

# Resources for SearchItems (includes editorial & customer reviews)
SEARCH_RESOURCES = [
    "Images.Primary.Medium",
    "Images.Primary.Large",
    "ItemInfo.Title",
    "ItemInfo.Features",
    "ItemInfo.ProductInfo",
    "ItemInfo.ByLineInfo",
    "ItemInfo.ManufactureInfo",
    #"EditorialReviews.EditorialReview",
    "CustomerReviews.Count",
    "CustomerReviews.StarRating",
]

# Resources for GetItems (no editorial/customer reviews support)
GETITEMS_RESOURCES = [
    "Images.Primary.Medium",
    "Images.Primary.Large",
    "ItemInfo.Title",
    "ItemInfo.Features",
    "ItemInfo.ProductInfo",
    "ItemInfo.ByLineInfo",
    "ItemInfo.ContentInfo",
]

# Comprehensive resources for complete product information
COMPLETE_RESOURCES = [
    # Images
    "Images.Primary.Small",
    "Images.Primary.Medium", 
    "Images.Primary.Large",
    "Images.Variants.Small",
    "Images.Variants.Medium",
    "Images.Variants.Large",
    
    # Basic ItemInfo resources
    "ItemInfo.Title",
    "ItemInfo.Features",
    "ItemInfo.ByLineInfo",
    "ItemInfo.Classifications",
    "ItemInfo.ContentInfo",
    "ItemInfo.ContentRating",
    "ItemInfo.ExternalIds",
    "ItemInfo.ManufactureInfo",
    "ItemInfo.ProductInfo",
    "ItemInfo.TechnicalInfo",
    "ItemInfo.TradeInInfo",
    
    # Offers (pricing information)
    "Offers.Listings.Availability.MaxOrderQuantity",
    "Offers.Listings.Availability.Message", 
    "Offers.Listings.Availability.MinOrderQuantity",
    "Offers.Listings.Availability.Type",
    "Offers.Listings.Condition",
    "Offers.Listings.Condition.ConditionNote",
    "Offers.Listings.Condition.SubCondition",
    "Offers.Listings.DeliveryInfo.IsAmazonFulfilled",
    "Offers.Listings.DeliveryInfo.IsFreeShippingEligible",
    "Offers.Listings.DeliveryInfo.IsPrimeEligible",
    "Offers.Listings.IsBuyBoxWinner",
    "Offers.Listings.MerchantInfo",
    "Offers.Listings.Price",
    "Offers.Listings.ProgramEligibility.IsPrimeExclusive",
    "Offers.Listings.ProgramEligibility.IsPrimePantry",
    "Offers.Listings.Promotions",
    "Offers.Listings.SavingBasis",
    "Offers.Summaries.HighestPrice",
    "Offers.Summaries.LowestPrice",
    "Offers.Summaries.OfferCount",
    
    # Browse Node Information
    "BrowseNodeInfo.BrowseNodes",
    "BrowseNodeInfo.BrowseNodes.Ancestor",
    "BrowseNodeInfo.BrowseNodes.SalesRank",
    "BrowseNodeInfo.WebsiteSalesRank",
    
    # Parent ASIN (for variations)
    "ParentASIN",
]


class PAAPIError(Exception):
    pass


def _sign(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def _get_signature_key(key: str, date_stamp: str, region_name: str, service_name: str) -> bytes:
    k_date = _sign(("AWS4" + key).encode("utf-8"), date_stamp)
    k_region = _sign(k_date, region_name)
    k_service = _sign(k_region, service_name)
    k_signing = _sign(k_service, "aws4_request")
    return k_signing


def _aws_v4_sign_generic(canonical_uri: str, target: str, payload: str, amz_date: str, date_stamp: str) -> Tuple[str, str, str]:
    canonical_querystring = ""
    headers_map = {
        "content-encoding": "amz-1.0",
        "content-type": "application/json; charset=utf-8",
        "host": PAAPI_HOST,
        "x-amz-date": amz_date,
        "x-amz-target": target,
    }
    sorted_items = sorted(headers_map.items())
    canonical_headers = "".join(f"{k}:{v}\n" for k, v in sorted_items)
    # IMPORTANT: In AWS SigV4, the signed headers list MUST be semicolon-delimited, not comma-delimited.
    # Using commas causes 'IncompleteSignature' because AWS cannot parse the components.
    signed_headers = ";".join(k for k, _ in sorted_items)
    payload_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    canonical_request = f"POST\n{canonical_uri}\n{canonical_querystring}\n{canonical_headers}\n{signed_headers}\n{payload_hash}"
    algorithm = "AWS4-HMAC-SHA256"
    credential_scope = f"{date_stamp}/{AMAZON_REGION}/ProductAdvertisingAPI/aws4_request"
    string_to_sign = f"{algorithm}\n{amz_date}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
    signing_key = _get_signature_key(AMAZON_SECRET_KEY, date_stamp, AMAZON_REGION, "ProductAdvertisingAPI")
    signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
    authorization_header = f"{algorithm} Credential={AMAZON_ACCESS_KEY}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}"
    return authorization_header, signed_headers, canonical_headers


def _aws_v4_sign_search(payload: str, amz_date: str, date_stamp: str) -> str:
    auth_header, _, _ = _aws_v4_sign_generic("/paapi5/searchitems", X_AMZ_TARGET_SEARCH, payload, amz_date, date_stamp)
    return auth_header


def _aws_v4_sign_getitems(payload: str, amz_date: str, date_stamp: str) -> str:
    auth_header, _, _ = _aws_v4_sign_generic("/paapi5/getitems", X_AMZ_TARGET_GET, payload, amz_date, date_stamp)
    return auth_header


def search_items(keyword: str, max_items: int = 15, retries: int = 3) -> List[Dict[str, Any]]:
    """Search items by keyword using PA-API.

    Returns list of raw item dicts. If credentials missing, returns empty list (fails soft).
    """
    if not all([AMAZON_ACCESS_KEY, AMAZON_SECRET_KEY, AMAZON_PARTNER_TAG]):
        print("[PAAPI] Missing Amazon credentials. Returning empty result.")
        return []

    payload_obj = {
        "Keywords": keyword,
        "PartnerTag": AMAZON_PARTNER_TAG,
        "PartnerType": "Associates",
        "Marketplace": "www.amazon.com",
        "Resources": SEARCH_RESOURCES,
        # Optional tuning fields
        "SearchIndex": "All",
        "ItemCount": max_items if max_items <= 10 else 10,
    }
    payload = json.dumps(payload_obj, separators=(",", ":"))

    attempt = 0
    while attempt <= retries:
        attempt += 1
        amz_dt = datetime.datetime.utcnow()
        amz_date = amz_dt.strftime("%Y%m%dT%H%M%SZ")
        date_stamp = amz_dt.strftime("%Y%m%d")
        auth_header = _aws_v4_sign_search(payload, amz_date, date_stamp)
        headers = {
            "content-encoding": "amz-1.0",
            "content-type": "application/json; charset=utf-8",
            "host": PAAPI_HOST,
            "x-amz-date": amz_date,
            "x-amz-target": X_AMZ_TARGET_SEARCH,
            "Authorization": auth_header,
        }
        # Debug (first attempt) helpful for 404 diagnosis
        if attempt == 1:
            print("[PAAPI] DEBUG Request headers:")
            for hk, hv in headers.items():
                if hk.lower() != 'authorization':
                    print(f"  {hk}: {hv}")
            print("[PAAPI] DEBUG Payload:")
            print(payload)
        try:
            resp = requests.post(PAAPI_ENDPOINT, data=payload, headers=headers, timeout=20)
            # Log raw body on client/server errors for debugging BEFORE retry/raise
            if resp.status_code >= 400:
                snippet = resp.text[:1000].replace('\n', ' ')
                print(f"[PAAPI] HTTP {resp.status_code} body snippet: {snippet}")
                # Try parse structured errors
                try:
                    jerr = resp.json()
                    errors = jerr.get('Errors') or jerr.get('Error') or []
                    if errors:
                        print("[PAAPI] Errors object:")
                        if isinstance(errors, list):
                            for eobj in errors:
                                if isinstance(eobj, dict):
                                    print("  - Code:", eobj.get('Code'), "Message:", eobj.get('Message'))
                                else:
                                    print("  -", eobj)
                        elif isinstance(errors, dict):
                            print("  - Code:", errors.get('Code'), "Message:", errors.get('Message'))
                except Exception:
                    pass

            if resp.status_code in (429, 500, 503):
                if attempt <= retries:
                    sleep_for = 2 ** (attempt - 1)
                    print(f"[PAAPI] Throttled/server error {resp.status_code}. Retry {attempt}/{retries} in {sleep_for}s...")
                    time.sleep(sleep_for)
                    continue
            resp.raise_for_status()
            data = resp.json()
            items = data.get("SearchResult", {}).get("Items") or data.get("ItemsResult", {}).get("Items") or []
            if not isinstance(items, list):
                print("[PAAPI] Unexpected items structure.")
                return []
            print(f"[PAAPI] Retrieved {len(items)} raw items.")
            return items[:max_items]
        except requests.RequestException as e:
            if attempt <= retries:
                sleep_for = 2 ** (attempt - 1)
                print(f"[PAAPI] Request error {e}. Retry {attempt}/{retries} in {sleep_for}s...")
                time.sleep(sleep_for)
                continue
            print(f"[PAAPI] Giving up after {attempt-1} retries: {e}")
            return []
        except Exception as e:  # noqa
            print(f"[PAAPI] Unexpected error: {e}")
            return []

    return []


def get_items_details(asins: List[str], retries: int = 2) -> List[Dict[str, Any]]:
    """Fetch item details for specific ASINs via GetItems endpoint."""
    if not asins:
        return []
    if not all([AMAZON_ACCESS_KEY, AMAZON_SECRET_KEY, AMAZON_PARTNER_TAG]):
        print("[PAAPI] Missing Amazon credentials. Returning empty result.")
        return []
    # PA-API allows up to 10 ASINs per request
    results: List[Dict[str, Any]] = []
    batch_size = 10
    for i in range(0, len(asins), batch_size):
        batch = asins[i:i+batch_size]
        payload_obj = {
            "ItemIds": batch,
            "PartnerTag": AMAZON_PARTNER_TAG,
            "PartnerType": "Associates",
            "Marketplace": "www.amazon.com",
            "Resources": GETITEMS_RESOURCES,
        }
        payload = json.dumps(payload_obj, separators=(",", ":"))
        attempt = 0
        while attempt <= retries:
            attempt += 1
            amz_dt = datetime.datetime.utcnow()
            amz_date = amz_dt.strftime("%Y%m%dT%H%M%SZ")
            date_stamp = amz_dt.strftime("%Y%m%d")
            auth_header = _aws_v4_sign_getitems(payload, amz_date, date_stamp)
            headers = {
                "content-encoding": "amz-1.0",
                "content-type": "application/json; charset=utf-8",
                "host": PAAPI_HOST,
                "x-amz-date": amz_date,
                "x-amz-target": X_AMZ_TARGET_GET,
                "Authorization": auth_header,
            }
            try:
                resp = requests.post(f"https://{PAAPI_HOST}/paapi5/getitems", data=payload, headers=headers, timeout=20)
                if resp.status_code >= 400:
                    snippet = resp.text[:800].replace('\n', ' ')
                    print(f"[PAAPI][GetItems] HTTP {resp.status_code} body snippet: {snippet}")
                if resp.status_code in (429, 500, 503):
                    if attempt <= retries:
                        sleep_for = 2 ** (attempt - 1)
                        print(f"[PAAPI][GetItems] Retry {attempt}/{retries} in {sleep_for}s...")
                        time.sleep(sleep_for)
                        continue
                resp.raise_for_status()
                data = resp.json()
                items = data.get("ItemsResult", {}).get("Items") or []
                print(f"[PAAPI][GetItems] Batch {i//batch_size+1}: {len(items)} items")
                results.extend(items)
                break
            except requests.RequestException as e:
                if attempt <= retries:
                    sleep_for = 2 ** (attempt - 1)
                    print(f"[PAAPI][GetItems] Request error {e}. Retry {attempt}/{retries} in {sleep_for}s...")
                    time.sleep(sleep_for)
                    continue
                print(f"[PAAPI][GetItems] Giving up batch {i//batch_size+1}: {e}")
                break
    return results


def get_complete_product_info(asins: List[str], retries: int = 2) -> List[Dict[str, Any]]:
    """
    Fetch comprehensive product information for specific ASINs using all available resources.
    
    This function requests all possible PA-API resources including:
    - All ItemInfo resources (Title, Features, Brand, Technical specs, etc.)
    - Images (all sizes and variants)
    - Offers and pricing information
    - Browse node and category information
    - Parent ASIN for variations
    
    Args:
        asins: List of ASINs to fetch
        retries: Number of retry attempts
        
    Returns:
        List of complete product information dictionaries
    """
    if not asins:
        return []
    if not all([AMAZON_ACCESS_KEY, AMAZON_SECRET_KEY, AMAZON_PARTNER_TAG]):
        print("[PAAPI] Missing Amazon credentials. Returning empty result.")
        return []
    
    print(f"[PAAPI] Fetching complete product information for {len(asins)} ASIN(s)...")
    print(f"[PAAPI] Using {len(COMPLETE_RESOURCES)} comprehensive resources...")
    
    results: List[Dict[str, Any]] = []
    batch_size = 10
    for i in range(0, len(asins), batch_size):
        batch = asins[i:i+batch_size]
        payload_obj = {
            "ItemIds": batch,
            "PartnerTag": AMAZON_PARTNER_TAG,
            "PartnerType": "Associates", 
            "Marketplace": "www.amazon.com",
            "Resources": COMPLETE_RESOURCES,
        }
        payload = json.dumps(payload_obj, separators=(",", ":"))
        attempt = 0
        while attempt <= retries:
            attempt += 1
            amz_dt = datetime.datetime.utcnow()
            amz_date = amz_dt.strftime("%Y%m%dT%H%M%SZ")
            date_stamp = amz_dt.strftime("%Y%m%d")
            auth_header = _aws_v4_sign_getitems(payload, amz_date, date_stamp)
            headers = {
                "content-encoding": "amz-1.0",
                "content-type": "application/json; charset=utf-8",
                "host": PAAPI_HOST,
                "x-amz-date": amz_date,
                "x-amz-target": X_AMZ_TARGET_GET,
                "Authorization": auth_header,
            }
            try:
                resp = requests.post(f"https://{PAAPI_HOST}/paapi5/getitems", data=payload, headers=headers, timeout=20)
                if resp.status_code >= 400:
                    snippet = resp.text[:800].replace('\n', ' ')
                    print(f"[PAAPI][Complete] HTTP {resp.status_code} body snippet: {snippet}")
                if resp.status_code in (429, 500, 503):
                    if attempt <= retries:
                        sleep_for = 2 ** (attempt - 1)
                        print(f"[PAAPI][Complete] Retry {attempt}/{retries} in {sleep_for}s...")
                        time.sleep(sleep_for)
                        continue
                resp.raise_for_status()
                data = resp.json()
                items = data.get("ItemsResult", {}).get("Items") or []
                print(f"[PAAPI][Complete] Batch {i//batch_size+1}: {len(items)} items with complete info")
                results.extend(items)
                break
            except requests.RequestException as e:
                if attempt <= retries:
                    sleep_for = 2 ** (attempt - 1)
                    print(f"[PAAPI][Complete] Request error {e}. Retry {attempt}/{retries} in {sleep_for}s...")
                    time.sleep(sleep_for)
                    continue
                print(f"[PAAPI][Complete] Giving up batch {i//batch_size+1}: {e}")
                break
    return results
