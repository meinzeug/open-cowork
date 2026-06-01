FROM ubuntu:22.04

# Setup non-interactive frontend
ENV DEBIAN_FRONTEND=noninteractive

# Update and install system dependencies
RUN apt-get update && apt-get install -y \
    xvfb \
    x11vnc \
    xfce4 \
    xfce4-terminal \
    thunar \
    mousepad \
    supervisor \
    curl \
    wget \
    git \
    python3 \
    python3-pip \
    python3-tk \
    scrot \
    xclip \
    xdotool \
    wmctrl \
    x11-utils \
    novnc \
    websockify \
    dbus-x11 \
    libasound2 \
    libdbus-glib-1-2 \
    libgtk-3-0 \
    libx11-xcb1 \
    libxt6 \
    && rm -rf /var/lib/apt/lists/*

# Install Firefox manually to avoid Snap package issues inside Docker
RUN wget -O /tmp/firefox.tar.bz2 "https://download.mozilla.org/?product=firefox-latest-ssl&os=linux64&lang=de" \
    && tar -jxvf /tmp/firefox.tar.bz2 -C /opt/ \
    && ln -s /opt/firefox/firefox /usr/local/bin/firefox \
    && rm /tmp/firefox.tar.bz2

# Create necessary directories
RUN mkdir -p /app /workspace /root/.config /var/log/supervisor

# Set up working directories
WORKDIR /app

# Copy sandbox agent requirements and install
COPY requirements.txt /app/
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy sandbox agent server code and supervisor configuration
COPY sandbox_agent.py /app/
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose ports: VNC stream (6080) and Sandbox Agent REST API (5001)
EXPOSE 6080 5001

# Start supervisord to launch all desktop services
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
