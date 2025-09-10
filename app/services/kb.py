from typing import Optional, Tuple, List
from .feed import feed_service
import logging
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Comprehensive MyPursu Knowledge Base
KB = [
    # Service Information
    ("scan_pay", "Scan & Pay: Accept secure UPI, cards & wallet payments from customers. Perfect for merchants to receive payments instantly. Supports all major payment methods including UPI, credit/debit cards, and digital wallets."),
    ("pay_to_upi", "Pay to UPI: Send money directly to any UPI ID instantly. Just enter the UPI ID and amount to transfer money securely. Works with all UPI apps like Google Pay, PhonePe, Paytm, etc."),
    ("pay_to_static_qr", "Pay to Static QR: Pay using QR codes for quick transactions. Scan any QR code to make instant payments. Ideal for shopping, dining, and bill payments at merchant locations."),
    ("concierge_package", "Concierge Package: Premium service offering personal assistance for all your needs in India. Includes bill payments, travel bookings, mailbox services, and more. Perfect for NRIs who need comprehensive support."),
    ("bill_payments", "Bill Payments: Pay all your utility bills instantly - electricity, water, gas, internet, mobile recharge, DTH, and more. Set up auto-pay for recurring bills. Available 24/7."),
    ("travel_bookings", "Travel Bookings: Book flights, hotels, cabs, and trains seamlessly. Compare prices, get best deals, and manage all your travel needs in one place. Includes domestic and international bookings."),
    ("mailbox", "Mailbox Services: Get your own personal Indian address to receive parcels and mail. We'll receive, store, and forward your packages safely. Perfect for online shopping and important documents."),
    ("pack_n_ship", "Pack N Ship: Convenient shipping solutions delivered right to your doorstep. Send packages anywhere in India or internationally. We handle packing, documentation, and delivery tracking."),
    ("withdraw", "Withdraw: Easy cash withdrawal from your MyPursu wallet. Use ATMs or partner locations to withdraw money. Low fees and instant processing available."),
    ("history", "History: View all your transaction history, payments, bookings, and service usage in one place. Download statements, track expenses, and manage your account activity."),
    ("remit2any", "Remit2Any: Send money to India from anywhere in the world. Competitive exchange rates, zero fees, and instant transfers. New users get $1 = ₹100+ for first $100. Existing users get $1 = ₹87.7."),
    
    # Pricing and Offers
    ("new_user_offers", "New User Offers: Get ₹640/kg for first courier shipment, ₹850 sign-up bonus, and exclusive exchange rates. Concierge Package offers $1 = ₹92 for first $100. Limited time offers available."),
    ("exchange_rates", "Exchange Rates: New users get $1 = ₹100 or more for first $100 transfer. Existing users get $1 = ₹87.7. Rates are updated regularly and are among the best in the market."),
    ("fees", "Fees: Zero fees on all Remit2Any transactions. Low fees for other services. Transparent pricing with no hidden charges. Check individual service pages for detailed fee structure."),
    
    # Account and KYC
    ("signup_process", "Sign Up Process: Create account with email or Gmail login. Complete KYC with valid documents. USA users need Driver's License, Passport, or Visa. India users need PAN and Aadhar/Driver's License/Passport/Voter ID."),
    ("kyc_requirements", "KYC Requirements: USA - US Driver's License, US Passport, or Visa with Foreign Passport. India - Valid PAN and one of: Aadhar, Driver's License, Passport, or Voter ID. Required for compliance and security."),
    ("account_verification", "Account Verification: Complete KYC process to verify your identity. This ensures secure transactions and compliance with regulations. Verification usually takes 24-48 hours."),
    
    # Support and Policies
    ("customer_support", "Customer Support: 24/7 support available via chat, email, and phone. Our team helps with account issues, transaction problems, and service guidance. Response time is typically under 2 hours."),
    ("refund_policy", "Refund Policy: Refunds are processed within 7-10 business days for unused services. Processing fees may apply. Contact support for refund requests with transaction details."),
    ("security", "Security: Bank-level encryption, secure servers, and fraud protection. All transactions are monitored and protected. Your personal and financial information is safe with us."),
    ("privacy_policy", "Privacy Policy: We protect your personal information and never share it with third parties without consent. All data is encrypted and stored securely. You can request data deletion anytime."),
    
    # Technical Support
    ("app_download", "App Download: Download MyPursu app from Google Play Store or Apple App Store. Available for Android and iOS devices. Regular updates with new features and improvements."),
    ("password_reset", "Password Reset: Use 'Forgot Password' link on login page. Reset email/SMS will be sent to your registered email/phone. Create strong password with letters, numbers, and symbols."),
    ("two_factor_auth", "Two-Factor Authentication: Enable 2FA for extra security. Receive OTP on your registered phone/email for login and sensitive transactions. Recommended for all users."),
    
    # Service Limits and Restrictions
    ("transaction_limits", "Transaction Limits: Daily limits vary by service and account verification level. Remit2Any: $10,000/day for verified users. Bill payments: ₹50,000/day. Contact support to increase limits."),
    ("supported_countries", "Supported Countries: Remit2Any supports 50+ countries including USA, UK, Canada, Australia, UAE, Singapore, and more. Check our website for complete list of supported countries."),
    ("supported_banks", "Supported Banks: All major Indian banks supported including SBI, HDFC, ICICI, Axis, Kotak, and 100+ other banks. Instant transfers to most banks."),
    
    # Common Issues and Solutions
    ("transaction_failed", "Transaction Failed: Check internet connection, sufficient balance, and correct recipient details. If issue persists, contact support with transaction ID. Most issues resolve within 24 hours."),
    ("kyc_rejected", "KYC Rejected: Ensure documents are clear, valid, and match your account details. Re-upload with better quality photos. Contact support if rejection reason is unclear."),
    ("app_not_working", "App Issues: Update to latest version, clear cache, restart device. If problems continue, uninstall and reinstall app. Contact support with device details and error messages."),
    
    # Business Information
    ("about_mypursu", "About MyPursu: Leading fintech platform serving NRIs worldwide. Founded to simplify financial services for Indians living abroad. Trusted by 100,000+ users across 50+ countries."),
    ("careers", "Careers: Join our growing team! We're hiring for engineering, product, marketing, and customer support roles. Remote and on-site positions available. Check our careers page for current openings."),
    ("partnership", "Partnership: Partner with MyPursu to offer our services to your customers. We provide APIs, white-label solutions, and referral programs. Contact our business team for partnership opportunities."),
]

def search_kb(query: str, top_k: int = 3) -> List[Tuple[str, str]]:
    """Enhanced search of the knowledge base with better scoring"""
    q = query.lower()
    scored = []
    
    # Extract keywords from query
    query_words = set(re.findall(r'\b\w+\b', q))
    
    for k, v in KB:
        # Combine key and value for search
        search_text = (k + " " + v).lower()
        
        # Calculate score based on multiple factors
        score = 0
        
        # Exact phrase matches get highest score
        if q in search_text:
            score += 10
        
        # Word matches
        for word in query_words:
            if len(word) > 2:  # Ignore short words
                if word in search_text:
                    score += 1
                # Bonus for word appearing in key
                if word in k.lower():
                    score += 2
        
        # Bonus for service-related keywords
        service_keywords = ['service', 'feature', 'how', 'what', 'where', 'when', 'why']
        for keyword in service_keywords:
            if keyword in q and keyword in search_text:
                score += 1
        
        if score > 0:
            scored.append((score, (k, v)))
    
    # Sort by score and return top results
    scored.sort(reverse=True, key=lambda x: x[0])
    return [kv for _, kv in scored[:top_k]]

def search_feed_kb(query: str, top_k: int = 3) -> List[Tuple[str, str]]:
    """
    Search the feed-based knowledge base using semantic search
    Returns list of (title, content) tuples
    """
    try:
        # Search feed entries
        results = feed_service.search_feed_entries(query, top_k)
        
        # Convert to (title, content) format for compatibility
        feed_results = []
        for result in results:
            # Use a snippet of content for better context
            content_snippet = result.content[:200] + "..." if len(result.content) > 200 else result.content
            feed_results.append((result.title, content_snippet))
        
        return feed_results
    except Exception as e:
        logger.error(f"Error searching feed KB: {e}")
        return []

def search_hybrid_kb(query: str, top_k: int = 3) -> List[Tuple[str, str]]:
    """
    Hybrid search combining basic KB and feed KB
    Returns combined results with feed results prioritized
    """
    try:
        # Get feed results (semantic search)
        feed_results = search_feed_kb(query, top_k)
        
        # Get basic KB results (keyword search)
        basic_results = search_kb(query, top_k)
        
        # Combine results, prioritizing feed results
        combined_results = []
        
        # Add feed results first (they're more comprehensive)
        combined_results.extend(feed_results)
        
        # Add basic KB results if we have room
        remaining_slots = top_k - len(feed_results)
        if remaining_slots > 0:
            combined_results.extend(basic_results[:remaining_slots])
        
        return combined_results[:top_k]
        
    except Exception as e:
        logger.error(f"Error in hybrid KB search: {e}")
        # Fallback to basic search
        return search_kb(query, top_k)

def get_relevant_context(query: str, max_chars: int = 500) -> str:
    """
    Get relevant context from both KB and feed for chatbot responses
    Returns formatted context string
    """
    try:
        # Get hybrid search results
        results = search_hybrid_kb(query, top_k=2)
        
        if not results:
            return ""
        
        # Format context
        context_parts = []
        for title, content in results:
            context_parts.append(f"From '{title}': {content}")
        
        context = " ".join(context_parts)
        
        # Truncate if too long
        if len(context) > max_chars:
            context = context[:max_chars-3] + "..."
        
        return context
        
    except Exception as e:
        logger.error(f"Error getting relevant context: {e}")
        return ""

def get_feed_stats() -> dict:
    """Get statistics about the feed knowledge base"""
    try:
        stats = feed_service.list_feed_entries(page=1, page_size=1, status="active")
        return {
            "total_feed_entries": stats.total,
            "feed_available": stats.total > 0
        }
    except Exception as e:
        logger.error(f"Error getting feed stats: {e}")
        return {
            "total_feed_entries": 0,
            "feed_available": False
        }

# ------------------ NEW FUNCTION ------------------
def fetch_website_content(url: str) -> str:
    """
    Fetch the text content of a webpage (like main site or FAQ) for KB ingestion.
    """
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove scripts and styles
        for script in soup(["script", "style"]):
            script.decompose()

        # Extract visible text
        text = soup.get_text(separator=" ", strip=True)
        return text
    except Exception as e:
        logger.error(f"Error fetching website content from {url}: {e}")
        return ""
