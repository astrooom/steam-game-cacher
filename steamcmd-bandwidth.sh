#!/bin/bash

# SteamCMD wrapper script with TC (Traffic Control) bandwidth limiting
# Environment variables for bandwidth control:
# BANDWIDTH_UP_RATE: Upload rate limit in KB/s (default: unlimited)
# BANDWIDTH_DOWN_RATE: Download rate limit in KB/s (default: unlimited) 
# BANDWIDTH_ENABLED: Set to "true" to enable bandwidth limiting (default: false)

# Function to verify tc is working
verify_tc() {
    echo "=== Traffic Control (TC) Verification ==="
    
    # Check if tc is installed
    if command -v tc >/dev/null 2>&1; then
        echo "✓ TC is installed: $(which tc)"
        echo "✓ TC version: $(tc -V 2>&1)"
    else
        echo "✗ TC is not installed!"
        return 1
    fi
    
    # Show current bandwidth limits if any
    if [ "$BANDWIDTH_ENABLED" = "true" ]; then
        echo "✓ Bandwidth limiting is ENABLED"
        echo "  - Upload rate: ${BANDWIDTH_UP_RATE:-unlimited} KB/s"
        echo "  - Download rate: ${BANDWIDTH_DOWN_RATE:-unlimited} KB/s"
    else
        echo "ℹ Bandwidth limiting is DISABLED"
    fi
    echo "======================================="
}

# Function to setup bandwidth limiting using tc
setup_bandwidth_limit() {
    local interface="eth0"
    
    # Clear any existing rules
    tc qdisc del dev $interface root 2>/dev/null || true
    
    if [ "$BANDWIDTH_ENABLED" = "true" ] && ([ -n "$BANDWIDTH_UP_RATE" ] || [ -n "$BANDWIDTH_DOWN_RATE" ]); then
        echo "Setting up bandwidth limiting on interface $interface..."
        
        # Convert KB/s to kbit/s (multiply by 8)
        if [ -n "$BANDWIDTH_DOWN_RATE" ]; then
            local down_kbits=$((BANDWIDTH_DOWN_RATE * 8))
            echo "  - Download limit: ${BANDWIDTH_DOWN_RATE} KB/s (${down_kbits} kbit/s)"
            
            # Setup download limiting using HTB (Hierarchical Token Bucket)
            tc qdisc add dev $interface root handle 1: htb default 30
            tc class add dev $interface parent 1: classid 1:1 htb rate ${down_kbits}kbit
            tc class add dev $interface parent 1:1 classid 1:10 htb rate ${down_kbits}kbit ceil ${down_kbits}kbit
            tc qdisc add dev $interface parent 1:10 handle 10: sfq perturb 10
            
            # Apply to all traffic
            tc filter add dev $interface protocol ip parent 1:0 prio 1 u32 match ip dst 0.0.0.0/0 flowid 1:10
        fi
        
        if [ -n "$BANDWIDTH_UP_RATE" ]; then
            local up_kbits=$((BANDWIDTH_UP_RATE * 8))
            echo "  - Upload limit: ${BANDWIDTH_UP_RATE} KB/s (${up_kbits} kbit/s)"
            # Note: Upload limiting in containers is more complex and may require additional setup
            echo "  - Upload limiting in containers requires special configuration"
        fi
        
        # Show current tc rules
        echo "✓ TC rules applied:"
        tc qdisc show dev $interface
        tc class show dev $interface
    fi
}

# Function to cleanup bandwidth limiting
cleanup_bandwidth_limit() {
    local interface="eth0"
    echo "Cleaning up bandwidth limiting..."
    tc qdisc del dev $interface root 2>/dev/null || true
    echo "✓ TC rules cleared"
}

# Always run verification to show tc status
verify_tc

# Trap to cleanup on exit
trap cleanup_bandwidth_limit EXIT

# Setup bandwidth limiting if enabled
setup_bandwidth_limit

# Show what we're about to execute
if [ "$BANDWIDTH_ENABLED" = "true" ] && ([ -n "$BANDWIDTH_UP_RATE" ] || [ -n "$BANDWIDTH_DOWN_RATE" ]); then
    echo ""
    echo "🔍 BANDWIDTH LIMITING VERIFICATION:"
    echo "Expected download rate: ${BANDWIDTH_DOWN_RATE:-unlimited} KB/s"
    if [ -n "$BANDWIDTH_DOWN_RATE" ]; then
        echo "Expected MB per minute: $(( BANDWIDTH_DOWN_RATE * 60 / 1024 )) MB/min"
    fi
    echo ""
    echo "Monitor actual bandwidth usage with:"
    echo "  - iftop: iftop -i eth0"
    echo "  - netstat: watch -n 1 'cat /proc/net/dev'"
    echo "  - tc stats: watch -n 1 'tc -s qdisc show dev eth0'"
    echo ""
fi

echo "Executing: steamcmd $*"

# Execute steamcmd directly (no wrapper needed with tc)
exec steamcmd "$@"
