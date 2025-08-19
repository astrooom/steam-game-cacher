FROM steamcmd/steamcmd:debian

# Install Traffic Control (TC) tools for bandwidth limiting
USER root

# Update package list and install bandwidth limiting and monitoring tools
RUN apt-get update && \
  apt-get install -y \
  iproute2 \
  iftop \
  net-tools \
  procps \
  psmisc \
  netcat-openbsd && \
  rm -rf /var/lib/apt/lists/*

# Create a wrapper script for bandwidth-limited steamcmd
COPY steamcmd-bandwidth.sh /usr/local/bin/steamcmd-bandwidth.sh
RUN chmod +x /usr/local/bin/steamcmd-bandwidth.sh

# Set the wrapper script as the default entrypoint
ENTRYPOINT ["/usr/local/bin/steamcmd-bandwidth.sh"]

