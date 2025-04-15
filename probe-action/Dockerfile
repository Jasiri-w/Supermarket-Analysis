FROM ghcr.io/puppeteer/puppeteer:17.0.0

COPY probe.js /home/pptruser/src/probe.js

WORKDIR /home/pptruser/src

ENTRYPOINT ["node", "/home/pptruser/src/probe.js"]
# ENTRYPOINT ["bash", "-c", "pwd && ls -l . && node /home/pptruser/src/probe.js"] for debugging