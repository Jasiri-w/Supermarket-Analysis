FROM ghcr.io/puppeteer/puppeteer:17.0.0

# Set working directory
WORKDIR /home/pptruser/src

# Copy files
COPY probe.js .

ENTRYPOINT [ "node", "probe.js" ]