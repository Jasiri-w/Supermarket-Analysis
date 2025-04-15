FROM ghcr.io/puppeteer/puppeteer:17.0.0

COPY ./probe-action/probe.js /home/pptruser/src/probe.js

WORKDIR /home/pptruser/src

ENTRYPOINT ["bash", "-c", "pwd && ls -l . && node probe.js"]