#!/bin/bash
# LDAP/LDAPS check script with JSON output
# Author: Walter Yao (adapted)
# Usage: ldapscheck.sh hostname port [netrace]

export CMD_RESULT="ldap_result.log"
export CMD_LOG="ldap_full.log"
declare -a failmsg
declare -a succmsg
declare -a action_plan
declare -a ldap_step

# Fail messages and action plan
failmsg=(
"ldap_connect_to_host: getaddrinfo failed"
"connect errno"
"TLS: could not load verify locations"
"TLS trace: SSL_connect:error in SSLv2/v3 write client hello"
"TLS trace: SSL_connect:error in SSLv2/v3 read server hello"
"TLS certificate verification: Error"
"ldap_bind: Invalid credentials"
"result: 32 No such object"
)
succmsg=(
"ldap_connect_to_host: Trying"
"connect success"
"TLS trace: SSL_connect:SSLv2/v3 write client hello"
"TLS trace: SSL_connect:SSLv3 read server hello"
"TLS trace: SSL_connect:SSLv3 read server certificate"
"res_errno: 0, res_error: <>, res_matched: <>"
"result: 0 Success"
)
action_plan=(
"STEP 1: Name resolution failed. Check DNS or /etc/hosts."
"STEP 2: TCP connection failed. Check ping/IP/port."
"STEP 3: TLS client certificate missing."
"STEP 4: TLS handshake error (client hello). Check firewall."
"STEP 5: TLS handshake error (server hello). Check firewall."
"STEP 6: TLS certificate verification failed. Upload correct certificate."
"STEP 7: Bind user/password incorrect."
"STEP 8: User not found. Check search base or username."
)
ldap_step=(
"STEP 1: Resolve hostname to IP"
"STEP 2: Establish TCP connection"
"STEP 3: Check TLS client certificate"
"STEP 4: TLS handshake (client hello)"
"STEP 5: TLS handshake (server hello)"
"STEP 6: TLS verify server certificate"
"STEP 7: LDAP bind user/password"
"STEP 8: LDAP search user existence"
)

# Detect failure
search_failure() {
    local line="$1"
    for i in "${!failmsg[@]}"; do
        if [[ "$line" =~ "${failmsg[i]}" ]]; then
            echo "{\"status\":\"fail\",\"step\":${i}+1,\"message\":\"${line}\",\"action\":\"${action_plan[i]}\"}"
            return 0
        fi
    done
    return 1
}

# Detect success
search_success() {
    local line="$1"
    for i in "${!succmsg[@]}"; do
        if [[ "$line" =~ "${succmsg[i]}" ]]; then
            echo "{\"status\":\"success\",\"step\":${i}+1,\"message\":\"${line}\"}"
            return 0
        fi
    done
    return 1
}

# Check log file and output JSON
check_output() {
    [ ! -f "$CMD_RESULT" ] && echo "{\"error\":\"$CMD_RESULT not found\"}" && exit 1
    mapfile -t cmd_out < "$CMD_RESULT"
    for line in "${cmd_out[@]}"; do
        search_failure "$line"
        search_success "$line"
    done
}

main() {
    if [ $# -lt 2 ]; then
        echo "{\"error\":\"Usage: $0 hostname port [netrace]\"}"
        exit 1
    fi

    local ldap_host="$1"
    local ldap_port="$2"
    local ldap_proto="ldaps"
    [ "$ldap_port" == "389" ] || [ "$ldap_port" == "3268" ] && ldap_proto="ldap"

    # Optional tcpdump
    if [ "$3" == "netrace" ]; then
        capture_file="/tmp/tcpdump-${ldap_host}_$(date +%Y%m%d_%H%M%S).pcap"
        timeout 10 tcpdump -c 200 -i any -w "$capture_file" &>/dev/null &
        sleep 5
    fi

    # LDAP password (env or prompt)
    LDAP_PASSWORD="${LDAP_PASSWORD:-}"
    if [ -z "$LDAP_PASSWORD" ]; then
        read -s -p "Enter LDAP password: " LDAP_PASSWORD
        echo
    fi

    # Run ldapsearch
    UNITY_LDAP_CRT="env LDAPTLS_CACERT=/EMC/backend/CEM/LDAPCer/serverCertificate.cer"
    $UNITY_LDAP_CRT ldapsearch -x -d 1 -v -H "$ldap_proto://$ldap_host:$ldap_port" \
        -b "CN=Walter Yao,CN=Users,dc=peeps,dc=lab" \
        -D "CN=Administrator,CN=Users,DC=peeps,DC=lab" \
        -w "$LDAP_PASSWORD" > "$CMD_RESULT" 2>&1

    # Check output
    check_output
}

main "$@"
