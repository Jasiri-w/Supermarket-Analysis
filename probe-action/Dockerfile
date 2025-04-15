FROM ghcr.io/puppeteer/puppeteer:17.0.0

WORKDIR /github/workspace/probe-action

COPY probe.js .

ENTRYPOINT ["bash", "-c", "pwd && ls -l . && node probe-action/probe.js"]