FROM ghcr.io/puppeteer/puppeteer:17.0.0

WORKDIR /home/pptruser/src

COPY probe.js .

ENTRYPOINT ["bash", "-c", "ls -R / && ls -R /github && node probe.js"]