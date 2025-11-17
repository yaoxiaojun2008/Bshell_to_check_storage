import re
import json

def analyze_ldap_log_json(text):
    """
    Analyze LDAP Tshark log and output result as JSON.
    """

    # Step detection patterns
    step_patterns = {
        "search_request": r"LDAPMessage searchRequest",
        "tcp_response": r"Reassembled TCP Segments|Len: \d{3,6}",
        "search_entry": r"LDAPMessage searchResEntry",
        "search_done": r"searchResDone|resultCode"
    }

    # Detect steps
    result = {step: False for step in step_patterns}
    for step, pat in step_patterns.items():
        if re.search(pat, text, re.DOTALL):
            result[step] = True

    # Collect returned DN entries
    entries = re.findall(r'searchResEntry.*?"(.*?)"', text, re.DOTALL)
    result["entries"] = entries

    # Determine overall result
    if result["search_request"] and result["tcp_response"] and result["search_entry"]:
        result["result"] = "success"
    else:
        result["result"] = "failed"

    return json.dumps(result, indent=4, ensure_ascii=False)


# Example usage:
if __name__ == "__main__":
    with open("ldap_log.txt", "r", encoding="utf-8") as f:
        log = f.read()
        print(analyze_ldap_log_json(log))
