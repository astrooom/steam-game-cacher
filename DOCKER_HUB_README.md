# SteamCMD with Bandwidth Limiting

**Official SteamCMD Debian image with Traffic Control (TC) bandwidth limiting capabilities.**

## What is this?

This image extends the official `steamcmd/steamcmd:debian` image with bandwidth limiting functionality using Linux Traffic Control (TC). It's literally just the official SteamCMD image with added networking tools and a wrapper script that allows you to limit download/upload speeds.

## Key Features

- ✅ **Based on official SteamCMD Debian image** - Same reliability and compatibility
- ✅ **Traffic Control (TC) bandwidth limiting** - Precise, kernel-level network control  
- ✅ **Easy to use** - Drop-in replacement for the official image
- ✅ **No performance overhead** - TC works at the network interface level
- ✅ **Container-friendly** - Designed specifically for Docker environments

## Quick Start

Simply replace your SteamCMD Docker image with this one and add bandwidth environment variables:

```bash
# Without bandwidth limiting (works exactly like official image)
docker run --rm -v /var/lib/steam_cache:/var/lib/steam_cache \
  astroom/steamcmd-bandwidth:latest \
  +force_install_dir /var/lib/steam_cache/740 \
  +login anonymous +app_update 740 validate +quit

# With bandwidth limiting (100 KB/s download limit)
docker run --rm --privileged \
  -e BANDWIDTH_ENABLED=true \
  -e BANDWIDTH_DOWN_RATE=100 \
  -v /var/lib/steam_cache:/var/lib/steam_cache \
  astroom/steamcmd-bandwidth:latest \
  +force_install_dir /var/lib/steam_cache/740 \
  +login anonymous +app_update 740 validate +quit
```

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `BANDWIDTH_ENABLED` | Enable bandwidth limiting | `true` |
| `BANDWIDTH_DOWN_RATE` | Download rate limit in KB/s | `1000` (1 MB/s) |
| `BANDWIDTH_UP_RATE` | Upload rate limit in KB/s | `500` (512 KB/s) |

## Use Cases

- **Game server hosting** - Control bandwidth usage when caching Steam games
- **Shared connections** - Limit SteamCMD to prevent it from saturating your network
- **Cost control** - Prevent unexpected bandwidth charges on metered connections
- **QoS compliance** - Ensure SteamCMD doesn't interfere with other services

## What's Added to the Base Image

This image adds the following packages to `steamcmd/steamcmd:debian`:

- `iproute2` - Traffic Control (TC) tools
- `iftop` - Network monitoring
- `net-tools` - Network utilities  
- `procps` - Process monitoring
- `psmisc` - Process utilities
- `netcat-openbsd` - Network testing

Plus a wrapper script (`steamcmd-bandwidth.sh`) that configures TC before running SteamCMD.

## Requirements

- **Privileged mode required** when using bandwidth limiting: `--privileged`
- **No special requirements** when bandwidth limiting is disabled

## Python Integration

This image is designed to work with the [steam-game-cacher](https://github.com/astrooom/steam-game-cacher) Python script, but works with any Docker setup.

## Source Code

- **GitHub**: [astrooom/steam-game-cacher](https://github.com/astrooom/steam-game-cacher)
- **Docker Hub**: [astroom/steamcmd-bandwidth](https://hub.docker.com/r/astroom/steamcmd-bandwidth)

## Tags

- `latest` - Latest stable version with Traffic Control bandwidth limiting

Built on top of the official SteamCMD image - just with bandwidth limiting superpowers! 🚀
