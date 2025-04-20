FROM ghcr.io/puppeteer/puppeteer:17.0.0

COPY probe.js /home/pptruser/src/probe.js

WORKDIR /home/pptruser/src

ENTRYPOINT ["/bin/bash", "-c", "\
  node /home/pptruser/src/probe.js > output.log 2>&1 && \
  cat output.log && \
  if grep -q 'App hibernating' output.log; then \
    echo 'wake_up_log=App hibernating. Attempting to wake up!' >> $GITHUB_OUTPUT; \
  else \
    echo 'No hibernation button found. App might already be active or the button is missing.' >> $GITHUB_OUTPUT; \
  fi \
"]
# ENTRYPOINT ["bash", "-c", "pwd && ls -l . && node /home/pptruser/src/probe.js"] for debugging
