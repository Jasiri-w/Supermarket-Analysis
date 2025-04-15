FROM ghcr.io/puppeteer/puppeteer:17.0.0

WORKDIR /github/workspace/probe-action

COPY probe.js .

ENTRYPOINT ["node", "probe.js"]