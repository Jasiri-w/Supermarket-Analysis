FROM ghcr.io/puppeteer/puppeteer:17.0.0

COPY probe.js /home/pptruser/src/probe.js

USER root

WORKDIR /home/pptruser/src

ENTRYPOINT ["/bin/bash", "-c", "\
  node /home/pptruser/src/probe.js > /tmp/output.log 2>&1 && \
  cat /tmp/output.log && \
  if grep -q 'App hibernating' /tmp/output.log; then \
    echo 'wake_up_log=App hibernating. Attempting to wake up!' >> $GITHUB_OUTPUT; \
  else \
    echo 'wake_up_log=No hibernation button found. App might already be active or the button is missing.' >> $GITHUB_OUTPUT; \
  fi \
"]

# ENTRYPOINT ["bash", "-c", "pwd && ls -l . && node /home/pptruser/src/probe.js"] for debugging
